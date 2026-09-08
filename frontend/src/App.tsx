import React, { useState } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { ChatLayout } from './components/layout/ChatLayout';
import { useChat } from './hooks/useChat';

export const App: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const {
    conversations,
    activeConversationId,
    currentMessages,
    isSubmitting,
    createNewChat,
    selectConversation,
    sendMessage,
    deleteConversation,
  } = useChat();

  return (
    <div className="h-screen w-full overflow-hidden bg-app text-text-primary flex font-sans">
      {/* Persistent / Responsive Navigation Sidebar */}
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewChat={createNewChat}
        onSelectConversation={selectConversation}
        onDeleteConversation={deleteConversation}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Workspace (Header + Content Workspace) */}
      <div className="flex-1 min-w-0 flex flex-col h-full overflow-hidden">
        <Header onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)} />
        <ChatLayout
          messages={currentMessages}
          isSubmitting={isSubmitting}
          onSendMessage={sendMessage}
          activeConversationId={activeConversationId}
        />
      </div>
    </div>
  );
};

export default App;
