import React, { useEffect, useRef } from 'react';
import './Dialog.css';

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  description?: React.ReactNode;
  children?: React.ReactNode;
  footer?: React.ReactNode;
  width?: 'sm' | 'md' | 'lg';
}

export const Dialog: React.FC<DialogProps> = ({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  width = 'md',
}) => {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    if (open) {
      el.showModal?.();
    } else {
      el.close?.();
    }
  }, [open]);

  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    const handle = () => onClose();
    el.addEventListener('close', handle);
    return () => el.removeEventListener('close', handle);
  }, [onClose]);

  const handleBackdrop = (e: React.MouseEvent<HTMLDialogElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  if (!open) return null;

  return (
    <dialog
      ref={dialogRef}
      className={`dialog dialog--${width}`}
      onClick={handleBackdrop}
      aria-modal="true"
    >
      <div className="dialog__panel">
        {title && (
          <div className="dialog__header">
            <h2 className="dialog__title label-mono">{title}</h2>
            <button className="dialog__close btn btn-ghost btn-icon" onClick={onClose} aria-label="Close">✕</button>
          </div>
        )}
        {description && <p className="dialog__desc">{description}</p>}
        {children && <div className="dialog__body">{children}</div>}
        {footer && <div className="dialog__footer">{footer}</div>}
      </div>
    </dialog>
  );
};
