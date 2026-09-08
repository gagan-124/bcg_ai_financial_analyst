import React from 'react';
import { FileText } from 'lucide-react';
import { SourceCitationData } from '../../types/financial';

export interface SourceCitationProps {
  source: SourceCitationData;
  className?: string;
}

export const SourceCitation: React.FC<SourceCitationProps> = ({
  source,
  className = '',
}) => {
  const parts = [
    source.sourceName,
    source.documentType,
    source.period,
    source.filingDate ? `Filed ${source.filingDate}` : undefined,
  ].filter(Boolean);

  return (
    <div
      className={`flex items-center gap-1.5 text-[11px] text-text-muted select-none ${className}`.trim()}
      aria-label={`Source citation: ${parts.join(', ')}`}
    >
      <FileText className="w-3.5 h-3.5 shrink-0 opacity-70" aria-hidden="true" />
      <span className="font-medium text-text-secondary">Source:</span>
      <span className="truncate">
        {parts.map((part, index) => (
          <React.Fragment key={index}>
            {index > 0 && <span className="mx-1 opacity-50">·</span>}
            <span>{part}</span>
          </React.Fragment>
        ))}
      </span>
    </div>
  );
};

export default SourceCitation;
