""" **ollama_model.py** """

import ollama


class OllamaModel:
    def __init__(self, model_path):
        self.model = ollama.load_model(model_path)

    def gerar_sql(self, prompt):
        return self.model.generate(prompt)
