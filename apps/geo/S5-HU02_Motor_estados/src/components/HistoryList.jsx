function HistoryList({ history }) {

  return (
    <div>
      <h3>Historial</h3>

      <ul>
        {history.map((item, index) => (
          <li key={index}>
            {item.estado} - {item.fecha} - {item.usuario}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default HistoryList;