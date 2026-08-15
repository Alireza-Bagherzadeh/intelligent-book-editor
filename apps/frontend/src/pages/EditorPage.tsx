import EditorPageIntro from "../components/editor/EditorPageIntro";
import EditorTipBanner from "../components/editor/EditorTipBanner";
import EditorWorkspace from "../components/editor/EditorWorkspace";
import Footer from "../components/layout/Footer";
import Header from "../components/layout/Header";

export default function EditorPage() {
  return (
    <div
      dir="rtl"
      className="min-h-screen bg-paper text-bodytext"
    >
      <Header />

      <main className="container-page pb-10 pt-28 lg:pt-32">
        <EditorPageIntro />
        <EditorWorkspace />
        <EditorTipBanner />
      </main>

      <Footer />
    </div>
  );
}
