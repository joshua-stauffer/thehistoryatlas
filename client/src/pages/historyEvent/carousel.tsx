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
    <ButtonGroup
      variant="text"
      sx={{
        width: "100%",
        "& .MuiButton-root": {
          fontFamily: "'Source Sans Pro', 'Helvetica Neue', sans-serif",
          fontSize: "1.1rem",
          fontWeight: 500,
          color: "#34495E",
          padding: "12px 24px",
          transition: "all 0.3s ease",
          borderColor: "rgba(0,0,0,0.08)",
          "&:hover": {
            backgroundColor: "rgba(52, 73, 94, 0.04)",
            color: "#8E44AD",
          },
        },
      }}
    >
      <Button
        sx={{
          marginLeft: "auto",
          borderRight: "none",
        }}
        startIcon={<ArrowBackIcon sx={{ transition: "all 0.3s ease" }} />}
        onClick={props.navigateLeft}
      >
        Previous Event
      </Button>
      <Button
        sx={{
          marginRight: "auto",
          borderLeft: "1px solid rgba(0,0,0,0.08)",
        }}
        endIcon={<ArrowForwardIcon sx={{ transition: "all 0.3s ease" }} />}
        onClick={props.navigateRight}
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
  const [emblaRef, emblaApi] = useEmblaCarousel({
    startIndex,
    loop: false,
    skipSnaps: false,
    dragFree: false,
    containScroll: "keepSnaps",
  });
  const [loadingMoreLeft, setLoadingMoreLeft] = useState(false);
  const [loadingMoreRight, setLoadingMoreRight] = useState(false);

  const handleScroll = useCallback(() => {
    if (!emblaApi) return;

    const currentIndex = emblaApi.selectedScrollSnap();
    setFocusedIndex(currentIndex);

    const canScrollPrev = emblaApi.canScrollPrev();
    const canScrollNext = emblaApi.canScrollNext();

    if (!canScrollPrev && !loadingMoreLeft) {
      setLoadingMoreLeft(true);
      loadPrev().finally(() => {
        setLoadingMoreLeft(false);
      });
    }

    if (!canScrollNext && !loadingMoreRight) {
      setLoadingMoreRight(true);
      loadNext().finally(() => {
        setLoadingMoreRight(false);
      });
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

    emblaApi.on("settle", handleScroll);

    return () => {
      emblaApi.off("settle", handleScroll);
    };
  }, [emblaApi, handleScroll]);

  const scrollPrev = useCallback(() => {
    if (emblaApi) emblaApi.scrollPrev();
  }, [emblaApi]);

  const scrollNext = useCallback(() => {
    if (emblaApi) emblaApi.scrollNext();
  }, [emblaApi]);

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
