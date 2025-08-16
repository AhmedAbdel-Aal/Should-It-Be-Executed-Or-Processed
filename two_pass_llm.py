import json 
import hashlib

class TwoPassFunctionalLLM:
    """
    Two-pass execution: Compile instruction → Execute on data
    The model NEVER sees both together
    """
    
    def __init__(self, model):
        self.model = model
        self.compiled_functions = {}
        
    def compile_instruction(self, instruction: str) -> dict:
        """
        Pass 1: Process ONLY the instruction to create an execution plan
        This happens ONCE per function definition
        """
        
        compilation_prompt = f"""
        Convert this instruction into a formal function specification.
        
        Instruction: {instruction}
        
        Output a JSON execution plan:
        {{
            "function_name": "<name>",
            "input_type": "<text|number|list|etc>",
            "processing_steps": ["step1", "step2", ...],
            "output_format": "<format>",
            "output_constraints": ["constraint1", ...],
            "extraction_pattern": "<what to extract>"
        }}
        """
        
        # Model sees ONLY instruction, no data
        execution_plan = self.model(compilation_prompt)
        
        # Parse and validate the plan
        #plan = json.loads(execution_plan.replace("```json", "").replace("```", ""))
        plan = execution_plan.strip()
        # Cache the compiled function
        function_id = hashlib.md5(instruction.encode()).hexdigest()
        self.compiled_functions[function_id] = plan
        
        return {
            'function_id': function_id,
            'plan': plan
        }
    
    def execute(self, function_id: str, data: str) -> str:
        """
        Pass 2: Execute the compiled function on data
        Model NEVER sees the original instruction, only the execution plan
        """
        
        if function_id not in self.compiled_functions:
            raise ValueError(f"Function {function_id} not compiled")
        
        plan = self.compiled_functions[function_id]
        
        # Create execution prompt WITHOUT the original instruction
        execution_prompt = f"""
        Execute the following computational plan on the provided data.
        
        EXECUTION PLAN: {plan}
        
        DATA TO PROCESS:
        {data}
        
        OUTPUT (following the plan exactly):
        """
        
        # Model sees plan + data, but NOT the original instruction
        # It cannot reinterpret what it's supposed to do
        result = self.model(execution_prompt)
        
        # Validate output matches plan constraints
        return result#self.validate_output(result, plan)
    

from openai import OpenAI

def llm_call_openai(user_prompt, model="gpt-3.5-turbo-0125"):
    print(f"backend used openai - {model}")
    client = OpenAI()

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user","content": user_prompt},
        ],
    )

    return completion.choices[0].message.content
