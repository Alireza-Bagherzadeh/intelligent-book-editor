import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import HeroSection from "@/components/home/HeroSection";
import ProductShowcaseSection from "@/components/home/ProductShowcaseSection";
import ProblemSection from "@/components/home/ProblemSection";
import WorkflowSection from "@/components/home/WorkflowSection";
import FeaturesSection from "@/components/home/FeaturesSection";
import BeforeAfterSection from "@/components/home/BeforeAfterSection";
import HumanInTheLoopSection from "@/components/home/HumanInTheLoopSection";
import TargetAudienceSection from "@/components/home/TargetAudienceSection";
import FinalCTASection from "@/components/home/FinalCTASection";

export default function HomePage() {
  return (
    <div className="home-shell min-h-screen bg-paper">
      <Header />
      <main>
        <HeroSection />
        <ProductShowcaseSection />
        <ProblemSection />
        <WorkflowSection />
        <FeaturesSection />
        <BeforeAfterSection />
        <HumanInTheLoopSection />
        <TargetAudienceSection />
        <FinalCTASection />
      </main>
      <Footer />
    </div>
  );
}
