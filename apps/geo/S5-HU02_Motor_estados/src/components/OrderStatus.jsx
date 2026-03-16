import { useState } from "react";
import StatusBadge from "./StatusBadge";
import HistoryList from "./HistoryList";

function OrderStatus() {

  const [status, setStatus] = useState("CREADO");
  const [history, setHistory] = useState([]);

  const role = "VENDEDOR";

  const changeStatus = (newStatus) => {

    const confirmChange = window.confirm(
      "¿Seguro que deseas cambiar el estado?"
    );

    if (!confirmChange) return;

    const record = {
      estado: newStatus,
      fecha: new Date().toLocaleString(),
      usuario: role
    };

    setStatus(newStatus);
    setHistory([...history, record]);
  };

  return (
    <div>
      <h2>Estado del pedido</h2>

      <StatusBadge status={status} />

      <h3>Cambiar estado</h3>

      {role === "VENDEDOR" && (
        <>
          <button onClick={() => changeStatus("CONFIRMADO")}>Confirmar</button>
          <button onClick={() => changeStatus("EN_PREPARACION")}>Preparar</button>
          <button onClick={() => changeStatus("EN_CAMINO")}>En camino</button>
          <button onClick={() => changeStatus("ENTREGADO")}>Entregado</button>
        </>
      )}

      <HistoryList history={history} />
    </div>
  );
}

export default OrderStatus;