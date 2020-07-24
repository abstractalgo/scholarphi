import React from "react";
import { PDFViewer } from "./types/pdfjs-viewer";
import * as uiUtils from "./utils/ui";

interface Props {
  pdfViewer: PDFViewer;
  handleSetTextSelection: (selection: Selection | null) => void;
  handleClearEntitySelection: () => void;
}

/**
 * Determine whether a click event targets a selectable element.
 */
function isClickEventInsideSelectable(event: MouseEvent) {
  return (
    event.target instanceof HTMLDivElement &&
    event.target.classList.contains("scholar-reader-annotation-span")
  );
}

/**
 * An overlay on top of the PDF Viewer containing widgets to be shown on top of the viewer, and
 * event handlers that trigger state changes based on click and keyboard
 * events. This overlay currently operates by adding event handlers to the container of
 * the PDF viewer generated by pdf.js. The component does not make any new DOM elements.
 *
 * In a past implementation, this component added a transparent overlay 'div' element on top of
 * the PDF viewer. That implementation was abandoned because the overlay intercepted click and
 * keyboard events that were meant for the page or for annotations on the page. In the current
 * implementation, clicks on the page or annotations will be processed by the page or annotation
 * *and* processed by this overlay, as in this overlay, event handlers are attached to a
 * parent element of all pages and annotations.
 */
class ViewerOverlay extends React.PureComponent<Props> {
  constructor(props: Props) {
    super(props);
    this.state = {
      viewerViewportUpdateTimeMs: Date.now(),
    };
    this.onClick = this.onClick.bind(this);
    this.onKeyUp = this.onKeyUp.bind(this);
    this.onSelectionChange = this.onSelectionChange.bind(this);
  }

  componentDidMount() {
    this.addEventListenersToViewer(this.props.pdfViewer);
  }

  componentDidUpdate(prevProps: Props) {
    if (prevProps.pdfViewer !== this.props.pdfViewer) {
      this.removeEventListenersForViewer(prevProps.pdfViewer);
      this.addEventListenersToViewer(this.props.pdfViewer);
    }
  }

  componentWillUnmount() {
    this.removeEventListenersForViewer(this.props.pdfViewer);
  }

  addEventListenersToViewer(pdfViewer: PDFViewer) {
    pdfViewer.container.addEventListener("click", this.onClick);
    pdfViewer.container.addEventListener("keyup", this.onKeyUp);
    /*
     * To capture changes in the selection within the document, there is no option other than
     * to listen to changes within the entire document. The W3C standards offer no way of listening
     * for selection changes within specific elements. See
     * https://w3c.github.io/selection-api/#user-interactions).
     */
    document.addEventListener("selectionchange", this.onSelectionChange);
  }

  removeEventListenersForViewer(pdfViewer: PDFViewer) {
    pdfViewer.container.removeEventListener("click", this.onClick);
    pdfViewer.container.removeEventListener("keyup", this.onKeyUp);
    document.removeEventListener("selectionchange", this.onSelectionChange);
  }

  onClick(event: MouseEvent) {
    const textSelection = document.getSelection();
    const clickIsInsideSelectable = isClickEventInsideSelectable(event);
    const clickIsInsideGloss =
      event.target instanceof HTMLElement &&
      uiUtils.findParentElement(event.target, (e) =>
        e.classList.contains("gloss")
      );

    if (
      !clickIsInsideSelectable &&
      !clickIsInsideGloss &&
      textSelection !== null &&
      textSelection.toString() === ""
    ) {
      this.props.handleClearEntitySelection();
    }
  }

  onKeyUp(event: KeyboardEvent) {
    if (uiUtils.isKeypressEscape(event)) {
      this.props.handleClearEntitySelection();
    }
  }

  onSelectionChange() {
    const selection = document.getSelection();
    if (selection === null) {
      this.props.handleSetTextSelection(null);
      return;
    }

    /**
     * Only set selection to non-null value if all selected ranges are of page text.
     */
    for (let i = 0; i < selection.rangeCount; i++) {
      const range = selection.getRangeAt(i);
      const textLayer = uiUtils.findParentElement(
        range.commonAncestorContainer,
        (e) => e.classList.contains("textLayer")
      );
      if (textLayer === null) {
        this.props.handleSetTextSelection(null);
        return;
      }
    }

    this.props.handleSetTextSelection(selection);
  }

  render() {
    return <>{this.props.children}</>;
  }
}

export default ViewerOverlay;
