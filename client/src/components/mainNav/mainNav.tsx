import { useHistory } from "react-router-dom";
import { Nav, Logo, LogoContainer, ButtonContainer } from "./style";
import { HistoryEntity } from "../../types";
import { MenuSearch } from "../../components/menuSearch/menuSearch";
import { addToHistory } from "../../hooks/history";

export const MainNav = () => {
  const history = useHistory();
  const handleEntityClick = (entity: HistoryEntity) => {
    addToHistory(entity);
    history.push("/");
  };
  return (
    <Nav>
      <LogoContainer>
        <Logo>The History Atlas</Logo>
      </LogoContainer>
      <MenuSearch handleEntityClick={handleEntityClick} />
    </Nav>
  );
};

/*
      <ButtonContainer>
        <MenuSearch handleEntityClick={handleEntityClick}/>
      </ButtonContainer>
      */
