function StatusBadge({ status }) {

  const colors = {
    CREADO: "gray",
    CONFIRMADO: "blue",
    EN_PREPARACION: "orange",
    EN_CAMINO: "purple",
    ENTREGADO: "green",
    CANCELADO: "red"
  };

  return (
    <span
      style={{
        backgroundColor: colors[status],
        color: "white",
        padding: "8px",
        borderRadius: "8px"
      }}
    >
      {status}
    </span>
  );
}

export default StatusBadge;