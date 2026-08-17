import React, { useState, useRef, useEffect } from 'react';
import './ReportChat.css';
import ReactMarkdown from 'react-markdown';

function ReportChat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hello. I am the MediIntel AI assistant. I can help answer questions based on your medical reports and trusted medical literature. Please remember I am an AI, not a doctor. **Consult your doctor** for any medical advice or diagnosis. How can I help you today?" }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedReportId, setSelectedReportId] = useState('00000000-0000-0000-0000-000000000000'); // Mocked ID
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMsg = { role: 'user', content: inputValue };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      // In a real app, you'd get the auth token here. We assume it's handled or omitted for this mock if not needed in dev
      // For MVP, if we don't have a real auth token, the backend @require_auth might block this.
      // Assuming for now the frontend has a way to call the API or the backend is bypassed in dev.
      // (Will need a mock token if require_auth is strict, but let's write the fetch first).
      
      const response = await fetch('http://localhost:5000/api/chatbot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          report_id: selectedReportId,
          message: userMsg.content,
          history: messages // Sending full history, backend limits to last 10
        })
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "I'm sorry, I encountered an error connecting to the server. Please ensure the backend is running and you are logged in." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h2>Report Chat</h2>
        <div className="report-selector">
          <label htmlFor="report-select">Active Report:</label>
          <select 
            id="report-select" 
            value={selectedReportId} 
            onChange={(e) => setSelectedReportId(e.target.value)}
          >
            <option value="00000000-0000-0000-0000-000000000000">Recent Blood Work (Mock)</option>
            <option value="11111111-1111-1111-1111-111111111111">Lipid Panel (Mock)</option>
          </select>
        </div>
      </header>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-bubble">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
            <div className="message-time">
              {msg.role === 'user' ? 'You' : 'MediIntel AI'}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="loading-indicator">
            <div className="dot"></div>
            <div className="dot"></div>
            <div className="dot"></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <form className="chat-form" onSubmit={handleSendMessage}>
          <input
            type="text"
            className="chat-input"
            placeholder="Ask about your report (e.g., What does high cholesterol mean?)"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className="send-btn" disabled={isLoading || !inputValue.trim()}>
            Send
          </button>
        </form>
        <div className="chat-disclaimer">
          AI generated information may be inaccurate. This is not medical advice. Always consult your doctor.
        </div>
      </div>
    </div>
  );
}

export default ReportChat;
