import { styles } from "../styles/styles.jsx";

export default function MessageBubble({ msg }) {
  return (
    <div
      style={{
        ...styles.messageRow,
        justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
      }}
    >
      {msg.role === "bot" && <div style={styles.botAvatar}>🤖</div>}
      <div
        style={{
          ...styles.bubble,
          ...(msg.role === "user" ? styles.userBubble : styles.botBubble),
        }}
      >
        <p style={styles.bubbleText}>{msg.text}</p>
        {msg.sources && msg.sources.length > 0 && (
          <div style={styles.sources}>
            <p style={styles.sourcesTitle}>📄 참고 데이터</p>
            {msg.sources.slice(0, 2).map((s, j) => (
              <p key={j} style={styles.sourceItem}>
                {s.content.slice(0, 60)}...
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}