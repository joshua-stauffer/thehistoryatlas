import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
  PropsWithChildren,
} from "react";
import { EngineType } from "embla-carousel/components/Engine";
import { EmblaCarouselType, EmblaOptionsType } from "embla-carousel";
import useEmblaCarousel from "embla-carousel-react";
import { EventView } from "./eventView";
import { Button, ButtonGroup, CircularProgress } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import { HistoryEvent } from "../../graphql/events";

type UsePrevNextButtonsType = {
  prevBtnDisabled: boolean;
  nextBtnDisabled: boolean;
  onPrevButtonClick: () => void;
  onNextButtonClick: () => void;
};

const usePrevNextButtons = (
  emblaApi: EmblaCarouselType | undefined,
  onButtonClick?: (emblaApi: EmblaCarouselType) => void
): UsePrevNextButtonsType => {
  const [prevBtnDisabled, setPrevBtnDisabled] = useState(true);
  const [nextBtnDisabled, setNextBtnDisabled] = useState(true);

  const onPrevButtonClick = useCallback(() => {
    if (!emblaApi) return;
    emblaApi.scrollPrev();
    if (onButtonClick) onButtonClick(emblaApi);
  }, [emblaApi, onButtonClick]);

  const onNextButtonClick = useCallback(() => {
    if (!emblaApi) return;
    emblaApi.scrollNext();
    if (onButtonClick) onButtonClick(emblaApi);
  }, [emblaApi, onButtonClick]);

  const onSelect = useCallback((emblaApi: EmblaCarouselType) => {
    setPrevBtnDisabled(!emblaApi.canScrollPrev());
    setNextBtnDisabled(!emblaApi.canScrollNext());
  }, []);

  useEffect(() => {
    if (!emblaApi) return;

    onSelect(emblaApi);
    emblaApi.on("reInit", onSelect);
    emblaApi.on("select", onSelect);
  }, [emblaApi, onSelect]);

  return {
    prevBtnDisabled,
    nextBtnDisabled,
    onPrevButtonClick,
    onNextButtonClick,
  };
};

type PropType = PropsWithChildren<
  React.DetailedHTMLProps<
    React.ButtonHTMLAttributes<HTMLButtonElement>,
    HTMLButtonElement
  >
>;

type CarouselPropType = {
  slides: JSX.Element[];
  options?: EmblaOptionsType;
  setFocusedIndex: (index: number) => void;
  startIndex: number;
  loadNext: () => void;
  loadPrev: () => void;
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

const EmblaCarousel: React.FC<CarouselPropType> = (props) => {
  const { slides, setFocusedIndex, startIndex, loadNext, loadPrev } = props;
  const scrollListenerRef = useRef<() => void>(() => undefined);
  const listenForScrollRef = useRef(true);

  const hasMoreToLoadRightRef = useRef(true);
  const [hasMoreToLoadRight, setHasMoreToLoadRight] = useState(true);
  const [loadingMoreRight, setLoadingMoreRight] = useState(false);
  const hasMoreToLoadLeftRef = useRef(true);
  const [hasMoreToLoadLeft, setHasMoreToLoadLeft] = useState(true);
  const [loadingMoreLeft, setLoadingMoreLeft] = useState(false);

  const options: EmblaOptionsType = {
    dragFree: false,
    containScroll: "keepSnaps",
    watchSlides: false,
    watchResize: false,
    startIndex: startIndex,
    inViewThreshold: 0, // default
  };

  const [emblaRef, emblaApi] = useEmblaCarousel({
    ...options,
    watchSlides: (emblaApi) => {
      const reloadEmbla = (): void => {
        const oldEngine = emblaApi.internalEngine();

        emblaApi.reInit();
        const newEngine = emblaApi.internalEngine();
        const copyEngineModules: (keyof EngineType)[] = [
          "location",
          "target",
          "scrollBody",
        ];
        copyEngineModules.forEach((engineModule) => {
          Object.assign(newEngine[engineModule], oldEngine[engineModule]);
        });

        newEngine.translate.to(oldEngine.location.get());
        const { index } = newEngine.scrollTarget.byDistance(0, false);
        newEngine.index.set(index);
        newEngine.animation.start();

        setLoadingMoreRight(false);
        setLoadingMoreLeft(false);
        listenForScrollRef.current = true;
      };

      const reloadAfterPointerUp = (): void => {
        emblaApi.off("pointerUp", reloadAfterPointerUp);
        reloadEmbla();
      };

      const engine = emblaApi.internalEngine();

      if (hasMoreToLoadRightRef.current && engine.dragHandler.pointerDown()) {
        const boundsActive = engine.limit.reachedMax(engine.target.get());
        engine.scrollBounds.toggleActive(boundsActive);
        emblaApi.on("pointerUp", reloadAfterPointerUp);
      } else {
        reloadEmbla();
      }
    },
  });

  const {
    prevBtnDisabled,
    nextBtnDisabled,
    onPrevButtonClick,
    onNextButtonClick,
  } = usePrevNextButtons(emblaApi);

  const onScroll = useCallback(
    (emblaApi: EmblaCarouselType) => {
      if (!listenForScrollRef.current) return;

      setLoadingMoreRight((loadingMore) => {
        const lastSlide = emblaApi.slideNodes().length - 1;
        const lastSlideInView = emblaApi.slidesInView().includes(lastSlide);
        const loadMore = !loadingMore && lastSlideInView;
        if (loadMore) {
          listenForScrollRef.current = false;
          loadNext();
        }

        return loadingMore || lastSlideInView;
      });

      setLoadingMoreLeft((loadingMore) => {
        const firstSlideInView = emblaApi.slidesInView().includes(0);
        console.log({ firstSlideInView });
        const loadMore = !loadingMore && firstSlideInView;

        if (loadMore) {
          listenForScrollRef.current = false;

          loadPrev();
        }

        return loadingMore || firstSlideInView;
      });
    },
    [loadPrev, loadNext]
  );

  const addScrollListener = useCallback(
    (emblaApi: EmblaCarouselType) => {
      scrollListenerRef.current = () => onScroll(emblaApi);
      emblaApi.on("scroll", scrollListenerRef.current);
    },
    [onScroll]
  );

  useEffect(() => {
    if (!emblaApi) return;
    addScrollListener(emblaApi);

    const onResize = () => emblaApi.reInit();
    window.addEventListener("resize", onResize);
    emblaApi.on("destroy", () =>
      window.removeEventListener("resize", onResize)
    );
  }, [emblaApi, addScrollListener]);

  useEffect(() => {
    hasMoreToLoadRightRef.current = hasMoreToLoadRight;
  }, [hasMoreToLoadRight]);

  useEffect(() => {
    hasMoreToLoadLeftRef.current = hasMoreToLoadLeft;
  }, [hasMoreToLoadLeft]);

  const logScrollProgress = useCallback(
    (emblaApi) => {
      const slidesInView: number[] = emblaApi.slidesInView();
      setFocusedIndex(slidesInView[0]);
    },
    [emblaApi, setFocusedIndex]
  );

  useEffect(() => {
    if (emblaApi) emblaApi.on("slidesInView", logScrollProgress);
  }, [emblaApi, logScrollProgress]);

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
      <EventNavBar
        navigateLeft={onPrevButtonClick}
        navigateRight={onNextButtonClick}
      />

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
          {hasMoreToLoadLeft && (
            <div
              className={"embla-infinite-scroll"}
              style={{
                position: "relative",
                flex: "0 0 15rem",
                minWidth: 0,
                height: slideHeight,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {loadingMoreLeft && <CircularProgress />}
            </div>
          )}
          {slides.map((event, index) => (
            <div
              className="embla__slide"
              style={{
                flex: `0 0 ${slideSize}`,
                minWidth: 0,
                paddingLeft: slideSpacing,
              }}
              key={index}
            >
              <div className="embla__slide__number">{event}</div>
            </div>
          ))}
          {hasMoreToLoadRight && (
            <div
              className={"embla-infinite-scroll"}
              style={{
                position: "relative",
                flex: "0 0 15rem",
                minWidth: 0,
                height: slideHeight,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {loadingMoreRight && <CircularProgress />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmblaCarousel;
