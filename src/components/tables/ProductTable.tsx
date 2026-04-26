import React, { useState } from "react";
import { generateAIDescription } from "../../services/aiService";

interface Product {
  id?: string;
  name: string;
  description: string;
  price: number;
  category: string;
  image_file?: File | null;
  image_url?: string;
}

interface ProductTableProps {
  products: Product[];
  onProductUpdated?: (product: Product) => void;
}

const ProductTable: React.FC<ProductTableProps> = ({ products, onProductUpdated }) => {
  const [newProduct, setNewProduct] = useState<Product>({
    name: "",
    description: "",
    price: 0,
    category: "",
    image_file: null,
  });
  const [generatingAI, setGeneratingAI] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const handleSuggestAI = async () => {
    if (!newProduct.image_file && !newProduct.image_url) {
      setAiError("Por favor, selecciona una imagen antes de generar la descripción.");
      return;
    }

    setGeneratingAI(true);
    setAiError(null);

    try {
      const formData = new FormData();

      if (newProduct.image_file) {
        formData.append("image_file", newProduct.image_file);
      }

      if (newProduct.product_id) {
        formData.append("product_id", newProduct.product_id);
      }

      const result = await generateAIDescription(formData);
      setNewProduct((prev) => ({ ...prev, description: result }));
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Error al generar la descripción con IA.";
      setAiError(message);
    } finally {
      setGeneratingAI(false);
    }
  };

  return (
    <div>
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Descripción</th>
            <th>Precio</th>
            <th>Categoría</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product, index) => (
            <tr key={product.id ?? index}>
              <td>{product.name}</td>
              <td>{product.description}</td>
              <td>{product.price}</td>
              <td>{product.category}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div>
        <h3>Nuevo Producto</h3>
        <input
          type="text"
          placeholder="Nombre"
          value={newProduct.name}
          onChange={(e) => setNewProduct((prev) => ({ ...prev, name: e.target.value }))}
        />
        <textarea
          placeholder="Descripción"
          value={newProduct.description}
          onChange={(e) =>
            setNewProduct((prev) => ({ ...prev, description: e.target.value }))
          }
        />
        <input
          type="file"
          accept="image/*"
          onChange={(e) =>
            setNewProduct((prev) => ({
              ...prev,
              image_file: e.target.files?.[0] ?? null,
            }))
          }
        />
        <button onClick={handleSuggestAI} disabled={generatingAI}>
          {generatingAI ? "Generando descripción..." : "Sugerir descripción con IA"}
        </button>
        {aiError && <p style={{ color: "red" }}>{aiError}</p>}
      </div>
    </div>
  );
};

export default ProductTable;
