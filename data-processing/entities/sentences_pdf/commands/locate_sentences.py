# TODO - keep for development
from scripts import run_pipeline

import logging
import os.path
from dataclasses import dataclass
from typing import Iterator, List, Any, Dict

from common import directories, file_utils
from common.commands.base import ArxivBatchCommand
from common.types import ArxivId, BoundingBox, EntityLocationInfo, SerializableSymbol, Equation, HueLocationInfo, \
    RelativePath, Context
from entities.sentences.types import Sentence

from entities.sentences_pdf.bbox import SymbolWithBBoxes, Block
from entities.sentences_pdf.fuzzy_match import locate_sentences_fuzzy_ngram

from collections import defaultdict


@dataclass(frozen=True)
class LocationTask:
    tex_path: RelativePath
    arxiv_id: ArxivId
    pipeline_sentences: List[Sentence]
    pipeline_symbols: List[SerializableSymbol]
    pipeline_equations: List[Equation]
    pipeline_contexts: List[Context]
    symbol_id_to_symbol: Dict[str, SymbolWithBBoxes]
    equation_id_to_equation: Dict[str, SymbolWithBBoxes]
    blocks: List[Block]


# TODO; any type
class LocateSentencesCommand(ArxivBatchCommand[Any, Any]):
    @staticmethod
    def get_name() -> str:
        return "locate-sentences"

    @staticmethod
    def get_description() -> str:
        return "Find locations of sentences. Requires 'locate-equations', 'locate-sentences', etc to have been run."

    def get_arxiv_ids_dirkey(self) -> str:
        return "detected-sentences"

    def load(self) -> Iterator[LocationTask]:

        for arxiv_id in self.arxiv_ids:

            output_dir = directories.arxiv_subdir("sentences-locations", arxiv_id)
            file_utils.clean_directory(output_dir)

            pipeline_sentences = list(file_utils.load_from_csv(
                os.path.join(directories.arxiv_subdir(dirkey='detected-sentences', arxiv_id=arxiv_id), 'entities.csv'),
                Sentence)
            )

            _symbol_id_to_symbol_bboxes = dict(file_utils.load_locations(arxiv_id=arxiv_id, entity_name='symbols'))
            pipeline_symbols = list(file_utils.load_from_csv(
                os.path.join(directories.arxiv_subdir(dirkey='detected-symbols', arxiv_id=arxiv_id), 'entities.csv'),
                SerializableSymbol)
            )
            symbol_id_to_symbol = {
                f'{symbol.tex_path}-{symbol.id_}': SymbolWithBBoxes(text=f'${symbol.tex}$',
                                                                    bboxes=_symbol_id_to_symbol_bboxes[symbol.id_])
                for symbol in pipeline_symbols
            }

            _equation_id_to_equation_bboxes = dict(file_utils.load_locations(arxiv_id=arxiv_id, entity_name='equations'))
            pipeline_equations = list(file_utils.load_from_csv(
                os.path.join(directories.arxiv_subdir(dirkey='detected-equations', arxiv_id=arxiv_id), 'entities.csv'),
                Equation)
            )
            equation_id_to_equation = {
                equation.id_: SymbolWithBBoxes(text=equation.tex,
                                               bboxes=_equation_id_to_equation_bboxes[equation.id_])
                for equation in pipeline_equations
            }

            pipeline_contexts = list(file_utils.load_from_csv(
                os.path.join(directories.arxiv_subdir(dirkey='contexts-for-symbols', arxiv_id=arxiv_id), 'contexts.csv'),
                Context)
            )

            blocks = Block.build_blocks_from_spp_json(
                infile=os.path.join(directories.arxiv_subdir(dirkey='fetched-spp-jsons', arxiv_id=arxiv_id), 'spp.json')
            )

            yield LocationTask(arxiv_id=arxiv_id,
                               pipeline_sentences=pipeline_sentences,
                               pipeline_symbols=pipeline_symbols,
                               pipeline_equations=pipeline_equations,
                               pipeline_contexts=pipeline_contexts,
                               symbol_id_to_symbol=symbol_id_to_symbol,
                               equation_id_to_equation=equation_id_to_equation,
                               blocks=blocks)


    def process(self, item: LocationTask) -> Iterator[EntityLocationInfo]:

        sentence_id_to_bboxes = locate_sentences_fuzzy_ngram(pipeline_symbols=item.pipeline_symbols,
                                                             pipeline_equations=item.pipeline_equations,
                                                             pipeline_sentences=item.pipeline_sentences,
                                                             pipeline_contexts=item.pipeline_contexts,
                                                             symbol_id_to_symbol=item.symbol_id_to_symbol,
                                                             equation_id_to_equation=item.equation_id_to_equation,
                                                             blocks=item.blocks)

        for sentence_id, bboxes in sentence_id_to_bboxes:
            for bbox in bboxes:
                yield EntityLocationInfo(
                    tex_path="N/A",
                    entity_id=sentence_id,
                    page=bbox.page,
                    left=bbox.left,
                    top=bbox.top,
                    width=bbox.width,
                    height=bbox.height,
                )

    def save(self, item: LocationTask, result: EntityLocationInfo) -> None:
        output_dir = directories.arxiv_subdir("sentences-locations", item.arxiv_id)
        locations_path = os.path.join(output_dir, "entity_locations.csv")
        file_utils.append_to_csv(locations_path, result)
