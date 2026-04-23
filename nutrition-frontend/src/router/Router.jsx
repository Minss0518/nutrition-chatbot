import { BrowserRouter, Routes, Route } from "react-router-dom";
import ChatPage from "../pages/ChatPage.jsx";

export default function Router() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatPage />} />
      </Routes>
    </BrowserRouter>
  );
}