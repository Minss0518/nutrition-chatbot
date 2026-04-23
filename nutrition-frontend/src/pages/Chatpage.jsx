import { styles } from "../styles/styles.jsx";
import { useChat } from "../hooks/useChat.jsx";
import ChatHeader from "../components/ChatHeader.jsx";
import MessageList from "../components/MessageList.jsx";
import Suggestions from "../components/Suggestions.jsx";
import InputBar from "../components/InputBar.jsx";

export default function ChatPage() {
  const { messages, input, setInput, loading, bottomRef, sendMessage, handleKey } = useChat();

  return (
    <div style={styles.root}>
      <div style={styles.bgCircle1} />
      <div style={styles.bgCircle2} />

      <div style={styles.container}>
        <ChatHeader />

        <MessageList
          messages={messages}
          loading={loading}
          bottomRef={bottomRef}
        />

        {messages.length === 1 && (
          <Suggestions onSelect={sendMessage} />
        )}

        <InputBar
          input={input}
          setInput={setInput}
          onSend={sendMessage}
          onKeyDown={handleKey}
          loading={loading}
        />
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Noto Sans KR', sans-serif; }
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  );
}