import { NavLink } from "react-router-dom"

const navGroups = [
  {
    title: "Geography",
    items: [
      { to: "/currencies", label: "Currency" },
      { to: "/countries", label: "Country" },
      { to: "/states", label: "State" },
      { to: "/regions", label: "Region" },
      { to: "/routes", label: "Route" },
      { to: "/places", label: "Place" },
    ],
  },
  {
    title: "Organization",
    items: [
      { to: "/sections", label: "Section" },
      { to: "/companies", label: "Company" },
      { to: "/branch-types", label: "Branch Type" },
      { to: "/branches", label: "Branch" },
      { to: "/customers", label: "Customer" },
    ],
  },
  {
    title: "Production",
    items: [
      { to: "/works", label: "Work" },
      { to: "/quality-types", label: "Quality Type" },
      { to: "/distributions", label: "Distribution" },
      { to: "/schedulers", label: "Scheduler" },
      { to: "/case-studies", label: "Case Study" },
    ],
  },
]

export default function Sidebar() {
  return (
    <aside className="app-sidebar">
      <div className="app-sidebar-brand">
        <span className="app-sidebar-kicker">Masters</span>
        <span className="app-sidebar-title">Control Panel</span>
      </div>
      <nav className="app-sidebar-nav">
        {navGroups.map((group) => (
          <div key={group.title} className="app-nav-group">
            <p className="app-nav-group-title">{group.title}</p>
            {group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `app-nav-link${isActive ? " is-active" : ""}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  )
}
