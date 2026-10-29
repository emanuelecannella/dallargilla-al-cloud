/** Campo di un modulo con etichetta e suggerimento, sempre accessibile da tastiera e screen reader. */
export default function Campo({ etichetta, suggerimento, id, ...attributi }) {
  return (
    <div className="campo">
      <label htmlFor={id}>{etichetta}</label>
      <input id={id} name={id} {...attributi} />
      {suggerimento && <small>{suggerimento}</small>}
    </div>
  );
}
