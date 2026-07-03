import type { PageId } from "../constants/riskColors";

interface Props {
  current: PageId;
  onNavigate: (page: PageId) => void;
}

const NAV_ITEMS: { id: PageId; label: string; disabled?: boolean }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "map", label: "Safety Map" },
  { id: "incidents", label: "Incidents" },
];

export default function NavBar({ current, onNavigate }: Props) {
  return (
    <nav className="nav-bar" aria-label="Main navigation">
      {NAV_ITEMS.map((item) => (
        <button
          key={item.id}
          type="button"
          className={current === item.id ? "nav-active" : ""}
          disabled={item.disabled}
          onClick={() => !item.disabled && onNavigate(item.id)}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}
