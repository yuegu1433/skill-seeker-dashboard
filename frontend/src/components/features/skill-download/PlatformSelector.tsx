/**
 * PlatformSelector Component
 *
 * Platform selection dialog with icons, descriptions, and download progress tracking.
 * Supports all 4 platforms: Claude, Gemini, OpenAI, and Markdown.
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import type { Skill } from '@/types';
import './platform-selector.css';

export interface Platform {
  id: string;
  name: string;
  icon: string;
  description: string;
  supported: boolean;
  color: string;
  requirements?: string[];
  features?: string[];
}

interface PlatformSelectorProps {
  skill: Skill | null;
  isOpen: boolean;
  onClose: () => void;
  onDownload: (platform: string) => void;
}

const PLATFORMS: Platform[] = [
  {
    id: 'claude',
    name: 'Claude',
    icon: '🤖',
    description: 'Export for Anthropic Claude platform with optimized prompts',
    supported: true,
    color: '#D97706',
    requirements: ['Claude API access', 'Valid API key'],
    features: ['Prompt optimization', 'Context management', 'Function calling'],
  },
  {
    id: 'gemini',
    name: 'Gemini',
    icon: '💎',
    description: 'Export for Google Gemini platform with multi-modal support',
    supported: true,
    color: '#1A73E8',
    requirements: ['Google AI Studio access', 'API key'],
    features: ['Multi-modal input', 'RAG support', 'Batch processing'],
  },
  {
    id: 'openai',
    name: 'OpenAI',
    icon: '🔷',
    description: 'Export for OpenAI platform with GPT models',
    supported: true,
    color: '#10A37F',
    requirements: ['OpenAI API access', 'Valid API key'],
    features: ['Function calling', 'Fine-tuning ready', 'Streaming support'],
  },
  {
    id: 'markdown',
    name: 'Markdown',
    icon: '📝',
    description: 'Export as Markdown documentation with code blocks',
    supported: true,
    color: '#6B7280',
    requirements: ['None'],
    features: ['Documentation', 'Version control', 'Git friendly'],
  },
];

export const PlatformSelector: React.FC<PlatformSelectorProps> = ({
  skill,
  isOpen,
  onClose,
  onDownload,
}) => {
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    if (!selectedPlatform) return;

    setIsDownloading(true);
    try {
      await onDownload(selectedPlatform);
      onClose();
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setIsDownloading(false);
      setSelectedPlatform(null);
    }
  };

  const handleClose = () => {
    if (isDownloading) return;
    setSelectedPlatform(null);
    onClose();
  };

  const selectedPlatformInfo = PLATFORMS.find((p) => p.id === selectedPlatform);

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="large">
      <div className="platform-selector">
        <div className="platform-selector__header">
          <h2>Select Platform for Download</h2>
          {skill && <p className="platform-selector__skill-name">{skill.name}</p>}
        </div>

        <div className="platform-selector__content">
          <div className="platform-selector__grid">
            {PLATFORMS.map((platform) => (
              <div
                key={platform.id}
                className={`platform-card ${
                  selectedPlatform === platform.id ? 'selected' : ''
                } ${!platform.supported ? 'unsupported' : ''}`}
                onClick={() => platform.supported && setSelectedPlatform(platform.id)}
              >
                <div className="platform-card__header">
                  <div className="platform-card__icon" style={{ backgroundColor: platform.color }}>
                    {platform.icon}
                  </div>
                  <div className="platform-card__info">
                    <h3 className="platform-card__name">{platform.name}</h3>
                    {!platform.supported && (
                      <span className="platform-card__badge">Coming Soon</span>
                    )}
                  </div>
                  <div className="platform-card__radio">
                    <input
                      type="radio"
                      name="platform"
                      value={platform.id}
                      checked={selectedPlatform === platform.id}
                      onChange={() => platform.supported && setSelectedPlatform(platform.id)}
                      disabled={!platform.supported}
                    />
                  </div>
                </div>

                <p className="platform-card__description">{platform.description}</p>

                {platform.features && (
                  <div className="platform-card__features">
                    <h4>Features:</h4>
                    <ul>
                      {platform.features.map((feature) => (
                        <li key={feature}>✓ {feature}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {platform.requirements && (
                  <div className="platform-card__requirements">
                    <h4>Requirements:</h4>
                    <ul>
                      {platform.requirements.map((req) => (
                        <li key={req}>• {req}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>

          {selectedPlatformInfo && (
            <div className="platform-selector__details">
              <h3>Selected: {selectedPlatformInfo.name}</h3>
              <div className="platform-selector__summary">
                <div className="summary-item">
                  <span className="summary-label">Platform:</span>
                  <span className="summary-value">{selectedPlatformInfo.name}</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Format:</span>
                  <span className="summary-value">{selectedPlatformInfo.id.toUpperCase()}</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Size:</span>
                  <span className="summary-value">
                    {skill ? `${(skill.size / 1024).toFixed(2)} KB` : 'Unknown'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="platform-selector__footer">
          <Button variant="secondary" onClick={handleClose} disabled={isDownloading}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleDownload}
            disabled={!selectedPlatform || !selectedPlatformInfo?.supported || isDownloading}
          >
            {isDownloading ? 'Downloading...' : 'Download'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default PlatformSelector;
