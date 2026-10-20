type StatusProps = {
  open: boolean;
  // The details panel owns `open`; the status line only asks it to close.
  onClose: () => void;
};

export default function Status({ open, onClose }: StatusProps) {
  return (
    <p>
      Status: {open ? "open" : "closed"}{" "}
      <button type="button" onClick={onClose}>
        Close
      </button>
    </p>
  );
}
