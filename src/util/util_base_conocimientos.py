"""Retriever tool."""

from __future__ import annotations
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

from langchain_core.prompts import (
    BasePromptTemplate,
    PromptTemplate,
    aformat_document,
    format_document,
)
from langchain_core.tools.simple import Tool

if TYPE_CHECKING:
    from langchain_core.callbacks import Callbacks
    from langchain_core.documents import Document
    from langchain_core.retrievers import BaseRetriever


class RetrieverInput(BaseModel):
    """Input to the retriever."""

    query: str = Field(description="query to look up in retriever")


def _get_relevant_documents(
    query: str,
    retriever: BaseRetriever,
    document_prompt: BasePromptTemplate,
    document_separator: str,
    callbacks: Callbacks = None,
    response_format: Literal["content", "content_and_artifact"] = "content",
) -> str | tuple[str, list[Document]]:
    docs = retriever.invoke(query, config={"callbacks": callbacks})
    content = document_separator.join(
        format_document(doc, document_prompt) for doc in docs
    )
    if response_format == "content_and_artifact":
        return (content, docs)

    return content


async def _aget_relevant_documents(
    query: str,
    retriever: BaseRetriever,
    document_prompt: BasePromptTemplate,
    document_separator: str,
    callbacks: Callbacks = None,
    response_format: Literal["content", "content_and_artifact"] = "content",
) -> str | tuple[str, list[Document]]:
    docs = await retriever.ainvoke(query, config={"callbacks": callbacks})
    content = document_separator.join(
        [await aformat_document(doc, document_prompt) for doc in docs]
    )

    if response_format == "content_and_artifact":
        return (content, docs)

    return content


def create_retriever_tool(
    retriever: BaseRetriever,
    name: str,
    description: str,
    *,
    document_prompt: BasePromptTemplate | None = None,
    document_separator: str = "\n\n",
    response_format: Literal["content", "content_and_artifact"] = "content",
) -> Tool:

    document_prompt = document_prompt or PromptTemplate.from_template("{page_content}")

    def func(query: str, run_manager):
        return _get_relevant_documents(
            query=query,
            retriever=retriever,
            document_prompt=document_prompt,
            document_separator=document_separator,
            response_format=response_format,
            callbacks=run_manager
        )

    async def afunc(query: str, run_manager):
        return await _aget_relevant_documents(
            query=query,
            retriever=retriever,
            document_prompt=document_prompt,
            document_separator=document_separator,
            response_format=response_format,
            callbacks=run_manager
        )

    return Tool(
        name=name,
        description=description,
        func=func,
        coroutine=afunc,
        args_schema=RetrieverInput,
        response_format=response_format,
    )