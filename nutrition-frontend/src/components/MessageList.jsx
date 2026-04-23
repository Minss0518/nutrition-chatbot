import { styles } from "../styles/styles.jsx";
import MessageBubble from "./MessageBubble.jsx";

export default function MessageList({ messages, loading, bottomRef }) {
  return (
    <div style={styles.messages}>
      {messages.map((msg, i) => (
        <MessageBubble key={i} msg={msg} />
      ))}

      {loading && (
        <div style={{ ...styles.messageRow, justifyContent: "flex-start" }}>
          <div style={styles.botAvatar}>🤖</div>
          <div style={{ ...styles.bubble, ...styles.botBubble }}>
            <div style={styles.dots}>
              <span style={{ ...styles.dot, animationDelay: "0s" }} />
              <span style={{ ...styles.dot, animationDelay: "0.2s" }} />
              <span style={{ ...styles.dot, animationDelay: "0.4s" }} />
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}