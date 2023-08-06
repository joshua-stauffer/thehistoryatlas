import React from "react";
import { ThemeProvider } from "@mui/material/styles";

import { GenericError, ResourceNotFoundError } from "./pages/errorPages";
import { AddCitationPage } from "./pages/addCitation";
import { LoginPage } from "./pages/login";

import { useTokenManager } from "./hooks/token";

import { theme } from "./baseStyle";
import { NewFeed } from "./pages/newFeed/newFeed";
import { events } from "./data";

import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { LandingPage, landingPageLoader } from "./pages/newFeed/landingPage";
import { FeedData } from "./pages/newFeed/feedData";

function App() {
  const tokenManager = useTokenManager();
  const router = createBrowserRouter([
    {
      path: "/",
      element: <LandingPage />,
      loader: landingPageLoader,
    },
    {
      path: "/stories/:storyId/events/:eventId",
      element: <FeedData />,
      errorElement: <GenericError />,
    },
    {
      path: "/add-event",
      element: <AddCitationPage tokenManager={tokenManager} />,
    },
    {
      path: "/login",
      element: <LoginPage tokenManager={tokenManager} />,
    },
  ]);
  return (
    <ThemeProvider theme={theme}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

export default App;

// <Router>
//   <Switch>
//     <Route path="/login">
//       <LoginPage tokenManager={tokenManager} />
//     </Route>
//     <Route path="/add-citation">
//       <AddCitationPage tokenManager={tokenManager} />
//     </Route>
//     <Route path="/">
//       <NewFeed event={events[0]} next={() => null} prev={() => null} />
//     </Route>
//     <Route path="*">
//       <ResourceNotFoundError tokenManager={tokenManager} />
//     </Route>
//   </Switch>
// </Router>
