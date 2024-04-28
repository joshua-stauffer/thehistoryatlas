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
import { CircularProgress } from "@mui/material";

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

const PrevButton: React.FC<PropType> = (props) => {
  const { children, ...restProps } = props;

  return (
    <button
      className="embla__button embla__button--prev"
      type="button"
      {...restProps}
      style={{
        WebkitTapHighlightColor: "rgba(blue, 0.5)",
        WebkitAppearance: "none",
        appearance: "none",
        backgroundColor: "transparent",
        touchAction: "manipulation",
        display: "inline-flex",
        textDecoration: "none",
        cursor: "pointer",
        border: 0,
        padding: 0,
        margin: 0,
        boxShadow: "inset 0 0 0 0.2rem grey",
        width: "3.6rem",
        height: "3.6rem",
        zIndex: 1,
        borderRadius: "50%",
        color: "grey",
        // display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <svg className="embla__button__svg" viewBox="0 0 532 532">
        <path
          fill="currentColor"
          d="M355.66 11.354c13.793-13.805 36.208-13.805 50.001 0 13.785 13.804 13.785 36.238 0 50.034L201.22 266l204.442 204.61c13.785 13.805 13.785 36.239 0 50.044-13.793 13.796-36.208 13.796-50.002 0a5994246.277 5994246.277 0 0 0-229.332-229.454 35.065 35.065 0 0 1-10.326-25.126c0-9.2 3.393-18.26 10.326-25.2C172.192 194.973 332.731 34.31 355.66 11.354Z"
        />
      </svg>
      {children}
    </button>
  );
};

const NextButton: React.FC<PropType> = (props) => {
  const { children, ...restProps } = props;

  return (
    <button
      className="embla__button embla__button--next"
      type="button"
      {...restProps}
      style={{
        WebkitTapHighlightColor: "rgba(blue, 0.5)",
        WebkitAppearance: "none",
        appearance: "none",
        backgroundColor: "transparent",
        touchAction: "manipulation",
        display: "inline-flex",
        textDecoration: "none",
        cursor: "pointer",
        border: 0,
        padding: 0,
        margin: 0,
        boxShadow: "inset 0 0 0 0.2rem grey",
        width: "3.6rem",
        height: "3.6rem",
        zIndex: 1,
        borderRadius: "50%",
        color: "grey",
        // display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <svg
        className="embla__button__svg"
        viewBox="0 0 532 532"
        style={{ width: "35%", height: "35%" }}
      >
        <path
          fill="currentColor"
          d="M176.34 520.646c-13.793 13.805-36.208 13.805-50.001 0-13.785-13.804-13.785-36.238 0-50.034L330.78 266 126.34 61.391c-13.785-13.805-13.785-36.239 0-50.044 13.793-13.796 36.208-13.796 50.002 0 22.928 22.947 206.395 206.507 229.332 229.454a35.065 35.065 0 0 1 10.326 25.126c0 9.2-3.393 18.26-10.326 25.2-45.865 45.901-206.404 206.564-229.332 229.52Z"
        />
      </svg>
      {children}
    </button>
  );
};

const mockApiCall = (
  minWait: number,
  maxWait: number,
  callback: () => void
): void => {
  const min = Math.ceil(minWait);
  const max = Math.floor(maxWait);
  const wait = Math.floor(Math.random() * (max - min + 1)) + min;
  setTimeout(callback, wait);
};

type CarouselPropType = {
  slides: JSX.Element[];
  options?: EmblaOptionsType;
};

const EmblaCarousel: React.FC<CarouselPropType> = (props) => {
  const { slides: propSlides } = props;
  const scrollListenerRef = useRef<() => void>(() => undefined);
  const listenForScrollRef = useRef(true);
  const hasMoreToLoadRef = useRef(true);
  const [slides, setSlides] = useState(propSlides);
  const [hasMoreToLoad, setHasMoreToLoad] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const options: EmblaOptionsType = {
    dragFree: false,
    containScroll: "keepSnaps",
    watchSlides: false,
    watchResize: false,
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

        setLoadingMore(false);
        listenForScrollRef.current = true;
      };

      const reloadAfterPointerUp = (): void => {
        emblaApi.off("pointerUp", reloadAfterPointerUp);
        reloadEmbla();
      };

      const engine = emblaApi.internalEngine();

      if (hasMoreToLoadRef.current && engine.dragHandler.pointerDown()) {
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

  const onScroll = useCallback((emblaApi: EmblaCarouselType) => {
    if (!listenForScrollRef.current) return;

    setLoadingMore((loadingMore) => {
      const lastSlide = emblaApi.slideNodes().length - 1;
      const lastSlideInView = emblaApi.slidesInView().includes(lastSlide);
      const loadMore = !loadingMore && lastSlideInView;

      if (loadMore) {
        listenForScrollRef.current = false;

        mockApiCall(1000, 2000, () => {
          setSlides((currentSlides) => {
            if (currentSlides.length === 20) {
              setHasMoreToLoad(false);
              emblaApi.off("scroll", scrollListenerRef.current);
              return currentSlides;
            }
            return [...currentSlides, ...currentSlides];
          });
        });
      }

      return loadingMore || lastSlideInView;
    });
  }, []);

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
    hasMoreToLoadRef.current = hasMoreToLoad;
  }, [hasMoreToLoad]);

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
              key={index}
            >
              <div className="embla__slide__number">{event}</div>
            </div>
          ))}
          {hasMoreToLoad && (
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
              {loadingMore && <CircularProgress />}
            </div>
          )}
        </div>
      </div>

      <div
        className="embla__controls"
        style={{
          display: "grid",
          gridTemplateColumns: "auto 1fr",
          justifyContent: "space-between",
          gap: "1.2rem",
          marginTop: "1.8rem",
        }}
      >
        <div
          className="embla__buttons"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: "0.6rem",
            alignItems: "center",
          }}
        >
          <PrevButton onClick={onPrevButtonClick} disabled={prevBtnDisabled} />
          <NextButton onClick={onNextButtonClick} disabled={nextBtnDisabled} />
        </div>
      </div>
    </div>
  );
};

export default EmblaCarousel;
