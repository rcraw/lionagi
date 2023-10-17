from lionagi.session.Session import Session

class Scorer(Session):
    
    def __init__(self, system) -> None:
        super().__init__(system)

    def _score(self, 
            instruction, 
            session,  
            model="gpt-3.5-turbo-16k", 
            frequency_penalty=0, 
            function_call=None,
            functions=None, 
            n=1,
            stop=None,
            stream=False,
            temperature=1,
            top_p=1, 
            sleep=0.1):
        self.conversation.messages = session.conversation.messages
        self.conversation.change_system(self.conversation.system)
        self.conversation.add_messages(instruction=instruction)
        self.conversation.get_OpenAI_ChatCompletion(
            model=model, 
            frequency_penalty=frequency_penalty, 
            function_call=function_call,
            functions=functions, 
            n=n,
            stop=stop,
            stream=stream,
            temperature=temperature,
            top_p=top_p, 
            sleep=sleep)
        score = self.str_to_num(self.conversation.responses[-1]['content'])
        if isinstance(score, int):
            return score
        else: 
            raise ValueError(score)
    
    def score(self, 
            instruction, 
            session,  
            model="gpt-3.5-turbo-16k", 
            frequency_penalty=0, 
            function_call=None,
            functions=None, 
            n=1,
            stop=None,
            stream=False,
            temperature=1,
            top_p=1, 
            sleep=0.1, 
            num_tries=3):
        
        for i in range(num_tries):
            try:
                return self._score(
                    instruction=instruction, 
                    session=session,  
                    model=model, 
                    frequency_penalty=frequency_penalty, 
                    function_call=function_call,
                    functions=functions, 
                    n=n,
                    stop=stop,
                    stream=stream,
                    temperature=temperature,
                    top_p=top_p, 
                    sleep=sleep)
            except ValueError as e:
                print(f"Error: {e}")
                print(f"Attempt {i+1} of {num_tries}")
                continue

