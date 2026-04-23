import { styles } from "../styles/styles.jsx";

export default function ChatHeader() {
  return (
    <div style={styles.header}>
      <div style={styles.headerIcon}>🥗</div>
      <div>
        <h1 style={styles.headerTitle}>영양성분 챗봇</h1>
        <p style={styles.headerSub}>식품의약품안전처 DB 기반 · RAG 챗봇</p>
      </div>
      <div style={styles.statusBadge}>
        <span style={styles.statusDot} />
        Online
      </div>
    </div>
  );
}