""" **lm_studio_model.py:** """
import lm_studio


class LmStudioModel:
    def __init__(self, model_path):
        self.model = lm_studio.load_model(model_path)

    def gerar_sql(self, prompt):
        return self.model.generate(prompt)
