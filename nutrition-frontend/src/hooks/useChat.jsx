import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../api/chatApi.jsx";

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

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setLoading(true);

    try {
      const data = await sendChatMessage(question);
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: data.answer, sources: data.sources },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "❌ 서버 연결에 실패했습니다. FastAPI 서버가 실행 중인지 확인해주세요." },
      ]);
    } finally {
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