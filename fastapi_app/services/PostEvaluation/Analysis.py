import numpy as np
from sklearn.metrics import accuracy_score, cohen_kappa_score, mean_squared_error
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error

def calculate_metrics(human_scores, llm_scores):
    # Asegúrate de que las listas de calificaciones sean arrays de numpy para la facilidad de cálculo
    human_scores = np.array(human_scores)
    llm_scores = np.array(llm_scores)
    
    # Precisión (Accuracy)
    # En este caso, la precisión puede ser cuando las calificaciones son exactamente iguales
    accuracy = accuracy_score(human_scores, llm_scores)
    
    # Coeficiente de correlación de Pearson
    pearson_corr, _ = pearsonr(human_scores, llm_scores)
    
    # Cohen's Kappa (QWK)
    qwk = cohen_kappa_score(human_scores, llm_scores)
    
    # Sesgo: Evaluamos si el modelo tiende a sobrevalorar o subvalorar las calificaciones
    bias = np.mean(llm_scores - human_scores)
    
    # Error cuadrático medio (MSE)
    mse = mean_squared_error(human_scores, llm_scores)
    
    # Error absoluto medio (MAE)
    mae = mean_absolute_error(human_scores, llm_scores)
    
    # Raíz del error cuadrático medio (RMSE)
    rmse = np.sqrt(mse)

    # Imprimir las métricas calculadas
    print(f"Precisión (Exact Match): {accuracy * 100:.2f}%")
    print(f"Coeficiente de correlación de Pearson: {pearson_corr:.4f}")
    print(f"Cohen's Kappa (QWK): {qwk:.4f}")
    print(f"Sesgo (Bias): {bias:.4f}")
    print(f"Error cuadrático medio (MSE): {mse:.4f}")
    print(f"Error absoluto medio (MAE): {mae:.4f}")
    print(f"Raíz del error cuadrático medio (RMSE): {rmse:.4f}")

# Ejemplo de uso
# Calificaciones humanas y las asignadas por el LLM (como ejemplo)
human_scores = [90, 80, 70, 85, 95, 100, 60, 75, 88, 92]  # Calificaciones humanas
llm_scores = [88, 80, 72, 83, 94, 98, 62, 76, 89, 90]  # Calificaciones asignadas por el LLM

# Llamar a la función para calcular las métricas
calculate_metrics(human_scores, llm_scores)
