import { Navigate, Route, Routes } from "react-router-dom"
import Header from "./components/Header"
import Sidebar from "./components/Sidebar"
import BranchMaster from "./pages/BranchMaster"
import BranchTypeMaster from "./pages/BranchTypeMaster"
import CompanyMaster from "./pages/CompanyMaster"
import CountryMaster from "./pages/CountryMaster"
import CurrencyMaster from "./pages/CurrencyMaster"
import CustomerMaster from "./pages/CustomerMaster"
import PlaceMaster from "./pages/PlaceMaster"
import RegionMaster from "./pages/RegionMaster"
import RouteMaster from "./pages/RouteMaster"
import SectionMaster from "./pages/SectionMaster"
import StateMaster from "./pages/StateMaster"
import WorkMaster from "./pages/WorkMaster"
import QualityTypeMaster from "./pages/QualityTypeMaster"
import DistributionMaster from "./pages/DistributionMaster"
import SchedulerMaster from "./pages/SchedulerMaster"
import CaseStudyMaster from "./pages/CaseStudyMaster"

function App() {
  return (
    <div className="app-shell">
      <Header />
      <div className="app-body">
        <Sidebar />
        <main className="app-workspace">
          <Routes>
          <Route path="/" element={<Navigate to="/currencies" replace />} />
          <Route path="/currencies" element={<CurrencyMaster />} />
          <Route path="/countries" element={<CountryMaster />} />
          <Route path="/states" element={<StateMaster />} />
          <Route path="/regions" element={<RegionMaster />} />
          <Route path="/routes" element={<RouteMaster />} />
          <Route path="/places" element={<PlaceMaster />} />
          <Route path="/sections" element={<SectionMaster />} />
          <Route path="/companies" element={<CompanyMaster />} />
          <Route path="/branch-types" element={<BranchTypeMaster />} />
          <Route path="/branches" element={<BranchMaster />} />
          <Route path="/customers" element={<CustomerMaster />} />
          <Route path="/works" element={<WorkMaster />} />
          <Route path="/quality-types" element={<QualityTypeMaster />} />
          <Route path="/distributions" element={<DistributionMaster />} />
          <Route path="/schedulers" element={<SchedulerMaster />} />
          <Route path="/case-studies" element={<CaseStudyMaster />} />
          <Route
            path="/case-studies/:schedulerId/:detailId"
            element={<CaseStudyMaster />}
          />
        </Routes>
        </main>
      </div>
    </div>
  )
}

export default App
