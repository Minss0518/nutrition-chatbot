import { useState, useRef, useEffect } from "react";
import { sendChatMessageStream } from "../api/chatApi.jsx";

export function useChat() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "안녕하세요! 🥗 식품 영양성분 챗봇입니다.\n궁금한 식품의 영양정보를 물어보세요!",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const question = text || input.trim();
    if (!question || loading) return;

    // 1) 사용자 메시지 추가
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setLoading(true);

    // 2) 봇 메시지 빈칸으로 미리 추가
    setMessages((prev) => [...prev, { role: "bot", text: "", sources: [] }]);

    try {
      // ✅ 히스토리: 현재까지 쌓인 메시지 (빈 봇 메시지 제외)
      const history = messages
        .filter((m) => m.text)
        .map((m) => ({ role: m.role, text: m.text }));

      await sendChatMessageStream(question, history, {
        onToken: (chunk) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            updated[updated.length - 1] = {
              ...last,
              text: last.text + chunk,
            };
            return updated;
          });
        },

        onSources: (sources) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            updated[updated.length - 1] = { ...last, sources };
            return updated;
          });
        },

        onDone: () => {
          setLoading(false);
        },

        onError: (errMsg) => {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "bot",
              text: `❌ 오류가 발생했습니다: ${errMsg}`,
              sources: [],
            };
            return updated;
          });
          setLoading(false);
        },
      });
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "bot",
          text: "❌ 서버 연결에 실패했습니다. FastAPI 서버가 실행 중인지 확인해주세요.",
          sources: [],
        };
        return updated;
      });
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return { messages, input, setInput, loading, bottomRef, sendMessage, handleKey };
}
