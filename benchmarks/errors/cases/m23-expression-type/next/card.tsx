import type { ReactNode } from "react";

type CardProps = {
  title: string;
  count: number;
  footer: ReactNode;
  onHide: () => void;
};

export default function Card({ title, count, footer, onHide }: CardProps) {
  return (
    <div className="card">
      <p>
        {title + 1}: {count} tasks
      </p>
      <div className="card-footer">{footer}</div>
      <button type="button" onClick={onHide}>
        Hide
      </button>
    </div>
  );
}
