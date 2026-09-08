import React, { useState } from 'react';
import { Plus, MessageSquare, Settings, X, Info, Trash2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { Conversation } from '../../types';
import { STATIC_SHORTCUT_IDS } from '../../hooks/useChat';

export interface SidebarProps {
  conversations?: Conversation[];
  activeConversationId?: string | null;
  onNewChat?: () => void;
  onSelectConversation?: (id: string) => void;
  onDeleteConversation?: (id: string) => void;
  isOpen?: boolean;
  onClose?: () => void;
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations = [],
  activeConversationId = null,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  isOpen = false,
  onClose,
  className = '',
}) => {
  const [showSettingsNote, setShowSettingsNote] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleNewChat = () => {
    onNewChat?.();
    onClose?.();
  };

  const handleSelectConversation = (id: string) => {
    onSelectConversation?.(id);
    onClose?.();
  };

  const handleSettingsClick = () => {
    setShowSettingsNote((prev) => !prev);
    setTimeout(() => {
      setShowSettingsNote(false);
    }, 3000);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 md:hidden transition-opacity duration-150"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Surface */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 w-64 h-full bg-surface border-r border-border-hairline flex flex-col justify-between select-none transition-transform duration-200 ease-in-out md:translate-x-0 ${
          isOpen ? 'translate-x-0 shadow-neumorphic-elevated' : '-translate-x-full md:translate-x-0'
        } ${className}`.trim()}
      >
        {/* Top: Branding & Primary Actions */}
        <div className="p-4 space-y-5 overflow-hidden flex flex-col min-h-0">
          {/* Brand Header */}
          <div className="flex items-center justify-between shrink-0">
            <div className="flex flex-col">
              <span className="text-[17px] font-semibold tracking-tight text-text-primary">
                BCG AI
              </span>
              <span className="text-xs font-medium tracking-wider text-text-muted uppercase">
                Financial Analyst
              </span>
            </div>

            {/* Mobile Close Button */}
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className="p-1.5 rounded-sm text-text-muted hover:text-text-primary hover:bg-surface-hover md:hidden transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-interactive"
                aria-label="Close navigation sidebar"
              >
                <X className="w-[18px] h-[18px]" />
              </button>
            )}
          </div>

          {/* Primary Action Button */}
          <Button
            variant="solid"
            size="md"
            className="w-full justify-start font-medium text-sm shrink-0"
            onClick={handleNewChat}
          >
            <Plus className="w-[18px] h-[18px]" />
            <span>New Chat</span>
          </Button>

          {/* Navigation Section: Recent Conversations */}
          <nav className="space-y-1.5 pt-2 flex-1 min-h-0 flex flex-col" aria-label="Recent conversations">
            <span className="block px-2.5 text-xs font-medium tracking-wider text-text-muted uppercase shrink-0">
              Recent
            </span>
            <ul className="space-y-0.5 overflow-y-auto flex-1 pr-1">
              {conversations.map((conv) => {
                const isActive = conv.id === activeConversationId;
                const isStatic = (STATIC_SHORTCUT_IDS as readonly string[]).includes(conv.id);
                const isDeleting = deletingId === conv.id;

                if (isDeleting) {
                  return (
                    <li key={conv.id} className="py-0.5">
                      <div
                        className="flex items-center justify-between w-full px-2.5 py-1.5 text-xs bg-surface/90 border border-border-hairline rounded-md shadow-neumorphic-card select-none"
                        role="alert"
                      >
                        <span className="text-text-secondary truncate text-[11px] mr-1">
                          Delete analysis?
                        </span>
                        <div className="flex items-center gap-1.5 shrink-0">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeletingId(null);
                            }}
                            className="px-1.5 py-0.5 text-text-muted hover:text-text-primary rounded text-[11px] transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-interactive"
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteConversation?.(conv.id);
                              setDeletingId(null);
                            }}
                            className="px-2 py-0.5 bg-red-500/20 text-red-300 hover:bg-red-500/30 border border-red-500/30 rounded text-[11px] font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-red-400"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </li>
                  );
                }

                return (
                  <li key={conv.id}>
                    <div className="relative group w-full flex items-center">
                      <button
                        type="button"
                        onClick={() => handleSelectConversation(conv.id)}
                        className={`w-full flex items-center gap-2.5 py-2 text-sm rounded-md transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-interactive text-left truncate ${
                          !isStatic ? 'pr-8' : 'pr-2'
                        } ${
                          isActive
                            ? 'bg-surface-hover/80 text-text-primary font-medium border-l-2 border-primary-interactive pl-2 shadow-sm'
                            : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover/50 pl-2.5'
                        }`}
                        aria-current={isActive ? 'true' : undefined}
                      >
                        <MessageSquare
                          className={`w-4 h-4 shrink-0 ${
                            isActive ? 'text-accent-sage' : 'text-text-muted'
                          }`}
                        />
                        <span className="truncate">{conv.title}</span>
                      </button>

                      {!isStatic && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeletingId(conv.id);
                          }}
                          className="absolute right-1.5 p-1 rounded text-text-muted hover:text-red-400 hover:bg-surface-hover opacity-70 md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100 transition-opacity duration-150 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-interactive shrink-0"
                          aria-label={`Delete conversation "${conv.title}"`}
                          title="Delete conversation"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>

        {/* Bottom: Settings Anchor & Placeholder Popover */}
        <div className="p-3 border-t border-border-hairline relative">
          {showSettingsNote && (
            <div
              role="status"
              className="absolute bottom-full left-3 right-3 mb-2 p-2.5 bg-app border border-border-hairline rounded-md shadow-neumorphic-elevated text-xs text-text-secondary flex items-center gap-2 z-50 transition-opacity duration-150 pointer-events-none"
            >
              <Info className="w-3.5 h-3.5 text-accent-sage shrink-0" />
              <span>Settings will be available in a future release.</span>
            </div>
          )}
          <button
            type="button"
            onClick={handleSettingsClick}
            className="w-full flex items-center gap-2.5 px-3 py-2 text-sm font-normal text-text-secondary hover:text-text-primary hover:bg-surface-hover rounded-md transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-interactive text-left"
            aria-label="Settings"
            title="Settings will be available in a future release."
          >
            <Settings className="w-[18px] h-[18px] text-text-muted shrink-0" />
            <span>Settings</span>
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;

