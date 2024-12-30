import { redirect } from "react-router-dom";

export const LandingPage = () => {
  return <div></div>;
};

export const landingPageLoader = () => {
  return redirect(
    "/stories/9df8f0a3-cd99-4443-bb08-98d901dc363e/events/f423a520-006c-40d3-837f-a802fe299742"
  );
};
