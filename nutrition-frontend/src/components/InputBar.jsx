import { styles } from "../styles/styles.jsx";

export default function InputBar({ input, setInput, onSend, onKeyDown, loading }) {
  return (
    <div style={styles.inputRow}>
      <input
        style={styles.input}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="식품 영양성분을 물어보세요..."
        disabled={loading}
      />
      <button
        style={{
          ...styles.sendBtn,
          opacity: !input.trim() || loading ? 0.5 : 1,
        }}
        onClick={() => onSend()}
        disabled={!input.trim() || loading}
      >
        전송 ↑
      </button>
    </div>
  );
}