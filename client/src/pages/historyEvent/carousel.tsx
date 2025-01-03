import React, { useCallback, useEffect, useState } from "react";
import { EmblaOptionsType } from "embla-carousel";
import useEmblaCarousel from "embla-carousel-react";
import { Button, ButtonGroup } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";

type CarouselPropType = {
  slides: JSX.Element[];
  options?: EmblaOptionsType;
  setFocusedIndex: (index: number) => void;
  startIndex: number;
  loadNext: () => Promise<void>;
  loadPrev: () => Promise<void>;
};

type EventNavBarProps = {
  navigateLeft: () => void;
  navigateRight: () => void;
};

const EventNavBar = (props: EventNavBarProps) => {
  return (
    <ButtonGroup variant={"outlined"} sx={{ width: "100%" }}>
      <Button
        sx={{
          marginLeft: "auto",
        }}
        startIcon={<ArrowBackIcon />}
        onClick={props.navigateLeft}
        variant={"text"}
      >
        Previous Event
      </Button>
      <Button
        sx={{ marginRight: "auto" }}
        endIcon={<ArrowForwardIcon />}
        onClick={props.navigateRight}
        variant={"text"}
      >
        Next Event
      </Button>
    </ButtonGroup>
  );
};

const EmblaCarousel: React.FC<CarouselPropType> = ({
  slides,
  setFocusedIndex,
  startIndex,
  loadNext,
  loadPrev,
}) => {
  const [emblaRef, emblaApi] = useEmblaCarousel({ startIndex });
  const [loadingMoreLeft, setLoadingMoreLeft] = useState(false);
  const [loadingMoreRight, setLoadingMoreRight] = useState(false);

  const handleScroll = useCallback(() => {
    if (!emblaApi) return;

    const slidesInView = emblaApi.slidesInView();
    setFocusedIndex(slidesInView[0]);

    if (slidesInView.includes(0) && !loadingMoreLeft) {
      setLoadingMoreLeft(true);
      loadPrev().finally(() => setLoadingMoreLeft(false));
    }

    if (slidesInView.includes(slides.length - 1) && !loadingMoreRight) {
      setLoadingMoreRight(true);
      loadNext().finally(() => setLoadingMoreRight(false));
    }
  }, [
    emblaApi,
    setFocusedIndex,
    loadNext,
    loadPrev,
    loadingMoreLeft,
    loadingMoreRight,
  ]);

  useEffect(() => {
    if (!emblaApi) return;

    emblaApi.on("scroll", handleScroll);

    return () => {
      emblaApi.off("scroll", handleScroll);
    };
  }, [emblaApi, handleScroll]);

  const scrollPrev = () => {
    if (emblaApi) emblaApi.scrollPrev();
  };
  const scrollNext = () => {
    if (emblaApi) emblaApi.scrollNext();
  };

  const slideHeight = "19rem";
  const slideSpacing = "1rem";
  const slideSize = "100%";
  return (
    <div
      className="embla"
      style={{
        maxWidth: "48rem",
        margin: "auto",
      }}
    >
      <EventNavBar navigateLeft={scrollPrev} navigateRight={scrollNext} />

      <div
        className="embla__viewport"
        style={{ overflow: "hidden" }}
        ref={emblaRef}
      >
        <div
          className="embla__container"
          style={{
            backfaceVisibility: "hidden",
            display: "flex",
            touchAction: "pan-y",
            marginLeft: `calc(${slideSpacing} * -1)`,
          }}
        >
          {slides.map((event, index) => (
            <div
              className="embla__slide"
              style={{
                flex: `0 0 ${slideSize}`,
                minWidth: 0,
                paddingLeft: slideSpacing,
              }}
              key={index + 1}
            >
              <div className="embla__slide__number">{event}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default EmblaCarousel;
