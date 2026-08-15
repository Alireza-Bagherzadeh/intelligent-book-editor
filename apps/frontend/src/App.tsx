import HomePage from "./pages/HomePage";
import EditorPage from "./pages/EditorPage";
import { Route, Routes} from "react-router-dom";

function App() {
  return (
    <Routes>
    <Route path="/" element={<HomePage />} />
    <Route path="/editor" element={<EditorPage />} />
    </Routes>
  );

}

export default App;