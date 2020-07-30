import MuiDrawer from "@material-ui/core/Drawer";
import IconButton from "@material-ui/core/IconButton";
import ChevronRightIcon from "@material-ui/icons/ChevronRight";
import React from "react";
import EntityPropertyEditor from "./EntityPropertyEditor";
import FeedbackButton from "./FeedbackButton";
import { Entities, PaperId } from "./state";
import { Entity, EntityUpdateData } from "./types/api";
import { PDFViewer } from "./types/pdfjs-viewer";

export type DrawerMode = "open" | "closed";

interface Props {
  paperId: PaperId | undefined;
  pdfViewer: PDFViewer;
  mode: DrawerMode;
  entities: Entities | null;
  selectedEntityIds: string[];
  entityEditingEnabled: boolean;
  propagateEntityEdits: boolean;
  handleClose: () => void;
  handleScrollSymbolIntoView: () => void;
  handleSetPropagateEntityEdits: (propagate: boolean) => void;
  handleUpdateEntity: (
    entity: Entity,
    updates: EntityUpdateData
  ) => Promise<boolean>;
  handleDeleteEntity: (id: string) => Promise<boolean>;
}

export class Drawer extends React.PureComponent<Props> {
  constructor(props: Props) {
    super(props);
    this.closeDrawer = this.closeDrawer.bind(this);
  }

  componentWillUnmount() {
    const { pdfViewer } = this.props;
    if (pdfViewer != null) {
      this.removePdfPositioningForDrawerOpen(pdfViewer.container);
    }
  }

  positionPdfForDrawerOpen(
    pdfViewerContainer: HTMLElement,
    drawerContentType: string
  ) {
    pdfViewerContainer.classList.add(`drawer-${drawerContentType}`);
  }

  removePdfPositioningForDrawerOpen(pdfViewerContainer: HTMLElement) {
    pdfViewerContainer.classList.forEach((c) => {
      if (c.indexOf("drawer-") !== -1) {
        pdfViewerContainer.classList.remove(c);
      }
    });
  }

  closeDrawer() {
    if (this.props.mode !== "closed") {
      this.props.handleClose();
    }
  }

  render() {
    /**
     * The PDF viewer should know if the drawer is open so it can reposition the paper. Currently, we
     * notify the PDF viewer by adding a class, as the PDF viewer otherwise has no knowledge of the
     * state of this React application.
     */
    const {
      paperId,
      pdfViewer,
      mode,
      entities,
      selectedEntityIds,
      entityEditingEnabled,
    } = this.props;

    const feedbackContext = {
      mode,
      selectedEntityIds,
    };

    let firstSelectedEntity: Entity | null = null;
    if (entities !== null && selectedEntityIds.length > 0) {
      firstSelectedEntity = entities.byId[selectedEntityIds[0]] || null;
    }

    /*
     * Only one type of drawer content can appear at a time. This conditional block determines
     * which types of drawer content have precedence.
     */
    type DrawerContentType =
      | null
      | "entity-property-editor"
      | "symbol-search-results";
    let drawerContentType: DrawerContentType = null;
    if (entityEditingEnabled === true) {
      drawerContentType = "entity-property-editor";
    } else if (firstSelectedEntity === null) {
      drawerContentType = null;
    }

    if (pdfViewer != null) {
      if (mode === "open" && drawerContentType !== null) {
        this.removePdfPositioningForDrawerOpen(pdfViewer.container);
        this.positionPdfForDrawerOpen(pdfViewer.container, drawerContentType);
      } else {
        this.removePdfPositioningForDrawerOpen(pdfViewer.container);
      }
    }

    return (
      <MuiDrawer
        className="drawer"
        variant="persistent"
        anchor="right"
        /*
         * If for the drawer has been requested to open but there's nothing to show
         * in it, don't show it.
         */
        open={mode === "open" && drawerContentType !== null}
      >
        <div className="drawer__header">
          <div className="drawer__close_icon">
            <IconButton size="small" onClick={this.closeDrawer}>
              <ChevronRightIcon />
            </IconButton>
          </div>
          <FeedbackButton paperId={paperId} extraContext={feedbackContext} />
        </div>
        <div className="drawer__content">
          {drawerContentType === "entity-property-editor" && (
            <EntityPropertyEditor
              /*
               * When the selected entity changes, clear the property editor.
               */
              key={
                firstSelectedEntity !== null
                  ? firstSelectedEntity.id
                  : undefined
              }
              entity={firstSelectedEntity}
              propagateEntityEdits={this.props.propagateEntityEdits}
              handleSetPropagateEntityEdits={
                this.props.handleSetPropagateEntityEdits
              }
              handleSaveChanges={this.props.handleUpdateEntity}
              handleDeleteEntity={this.props.handleDeleteEntity}
            />
          )}
        </div>
      </MuiDrawer>
    );
  }
}

export default Drawer;
