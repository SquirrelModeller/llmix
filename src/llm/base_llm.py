from abc import abstractmethod

class BaseLLM():

    @abstractmethod
    def generate_response(self, input_text: str) -> str:
        """Generate response from input - implemented by providers"""
