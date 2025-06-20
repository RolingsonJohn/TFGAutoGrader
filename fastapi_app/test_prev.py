import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import Birch
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from services.PreEvaluation.CodeCleanner import CodeCleanner
from services.PreEvaluation.FileLoader import FileLoader
from services.PreEvaluation.CodeClassifier import CodeClassifier
import services.Config.Config as config
import joblib
from datetime import datetime

def extract_features_and_labels(code_classifier, files_dict, ref_code, method="transformer"):
    """
    Extrae features y etiquetas reales (0: válido, 1: no válido) y predice usando un árbol.
    """
    ref_embedding = (code_classifier.get_embedding(ref_code) 
                     if method == "transformer" 
                     else code_classifier.get_ngram_embedding(ref_code))

    X = []
    y_true = []
    y_pred = []

    for path, file_code in files_dict.items():
        clean_code = CodeCleanner.remove_comments(file_code)
        file_embedding = (code_classifier.get_embedding(clean_code) 
                        if method == "transformer" 
                        else code_classifier.get_ngram_embedding(clean_code))

        features = [
            code_classifier.euclidean_distance(ref_embedding, file_embedding),
            code_classifier.cosine_similitude(ref_embedding, file_embedding)
        ]

        X.append(features)
        # Etiquetado basado en la ruta del archivo
        label = 0 if "valid" in file_code.lower() else 1
        y_true.append(label)

    return np.array(X), np.array(y_true)

def reduce_and_plot(X, y, method='tsne', title="Embeddings reducidos"):
    if method == 'pca':
        reducer = PCA(n_components=2)
    elif method == 'tsne':
        perplexity = min(30, (len(X) - 1) // 3)
        if perplexity < 1:
            raise ValueError("No hay suficientes muestras para aplicar t-SNE.")
        reducer = TSNE(n_components=2, perplexity=perplexity, random_state=42)
    else:
        raise ValueError("Método de reducción no soportado.")

    X_reduced = reducer.fit_transform(X)

    plt.figure(figsize=(8, 6))
    colors = ['green' if label == 0 else 'red' for label in y]
    scatter = plt.scatter(X_reduced[:, 0], X_reduced[:, 1], c=colors, cmap='Set1', edgecolor='k', alpha=0.7)
    plt.title(title)
    plt.xlabel("Dim 1")
    plt.ylabel("Dim 2")
    plt.legend(*scatter.legend_elements(), title="Clases")
    plt.grid(True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plt.savefig(f"./outputs/{timestamp}_Embeddings.png")
    plt.close()

    return X_reduced

def plot_boundary(X, y, clf, scaler, title="Frontera del árbol"):
    if X.shape[1] != 2:
        print("La frontera de decisión solo puede visualizarse en 2D.")
        return

    X_scaled = scaler.fit_transform(X)

    x_min, x_max = X_scaled[:, 0].min() - 1, X_scaled[:, 0].max() + 1
    y_min, y_max = X_scaled[:, 1].min() - 1, X_scaled[:, 1].max() + 1
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 500),
                         np.linspace(y_min, y_max, 500))
    Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    plt.figure(figsize=(8, 6))
    plt.contourf(xx, yy, Z, alpha=0.3, cmap='Set1')
    
    colors = ['green' if label == 0 else 'red' for label in y]
    plt.scatter(X_scaled[:, 0], X_scaled[:, 1], c=colors, edgecolor='k', alpha=0.7)

    plt.title(title)
    plt.xlabel("Dim 1")
    plt.ylabel("Dim 2")
    plt.grid(True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plt.savefig(f"./outputs/{timestamp}_DecisionBoundary.png")
    plt.close()


def test_decission_tree(ref, files):

    tree = joblib.load(config.CLF_MODEL)
    classifier = CodeClassifier()
    
    X, y_true = extract_features_and_labels(classifier, files, ref_code=ref)
    
    y_pred = tree.predict(X)
    
    # Paso 2: Evaluación del árbol ya entrenado
    print("=== Evaluación del árbol ===")
    print(confusion_matrix(y_true, y_pred))
    print(classification_report(y_true, y_pred, target_names=["Valid", "Invalid"]))

    print(f"FICHEROS REALES\n{y_true}\n\n\nFICHEROS PREDICHOS\n{y_pred}")

    # Paso 3: Visualización con reducción (PCA/t-SNE)
    X_2d = reduce_and_plot(X, y_true, method='pca', title="Predicciones proyectadas")

    # Paso 4: Visualizar frontera de decisión del árbol
    scaler = StandardScaler()
    plot_boundary(X, y_true, tree, scaler)


def test_BIRCH(ref, files):
    classifier = CodeClassifier()
    X, y_true = extract_features_and_labels(classifier, files, ref_code=ref)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    birch = Birch(threshold=0.5, branching_factor=50, n_clusters=2)
    birch.fit(X_scaled)
    labels = birch.labels_

    print("=== Clustering BIRCH ===")
    print(f"Etiquetas de cluster: {labels}")
    print(f"Reales: {y_true}")

    # Visualización real vs clustering
    reduce_and_plot(X, y_true, method='pca', title="BIRCH - Reales (PCA)")
    reduce_and_plot(X, labels, method='pca', title="BIRCH - Clusters (PCA)")
    
    plot_boundary(X, y_true, birch, scaler, title="Frontera BIRCH")


def main():
    valid_files = FileLoader.load_files_from_dir("test/valid")
    invalid_files = FileLoader.load_files_from_dir("test/invalid")
    files = valid_files | invalid_files
    print(valid_files, invalid_files, files)
    ref = FileLoader.load_files(path="test/Fibonacci/good.c")

    test_decission_tree(ref, files)
    test_BIRCH(ref, files)
    


if __name__ == '__main__':
    main()
