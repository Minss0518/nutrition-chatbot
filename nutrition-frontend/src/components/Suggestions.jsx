import { styles } from "../styles/styles.jsx";

const SUGGESTIONS = [
  "닭가슴살 100g의 단백질 함량은?",
  "칼로리가 낮은 음식 추천해줘",
  "피자 중에 칼로리가 가장 높은 3가지 피자 알려줘",
];

export default function Suggestions({ onSelect }) {
  return (
    <div style={styles.suggestions}>
      {SUGGESTIONS.map((s, i) => (
        <button key={i} style={styles.suggestionBtn} onClick={() => onSelect(s)}>
          {s}
        </button>
      ))}
    </div>
  );
}