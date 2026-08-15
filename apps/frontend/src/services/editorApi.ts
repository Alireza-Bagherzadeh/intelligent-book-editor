import type {
  EditorIssue,
  EditorResult,
} from "../types/editor";

/**
 * Backend API base URL
 *
 * Default:
 * http://127.0.0.1:8000/api/v1
 *
 * Can be overridden with:
 * VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
 */
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000/api/v1"
).replace(/\/+$/, "");

/**
 * Polling configuration
 */
const PARSING_POLL_INTERVAL_MS = 1000;
const PARSING_MAX_ATTEMPTS = 60;

const REVIEW_POLL_INTERVAL_MS = 1500;
const REVIEW_MAX_ATTEMPTS = 80;

/**
 * Because the backend currently has no dedicated
 * review-status endpoint, we allow a short minimum
 * review time before considering reviewed blocks.
 */
const REVIEW_MIN_WAIT_MS = 3000;

const DIFFERENCES_POLL_INTERVAL_MS = 750;
const DIFFERENCES_MAX_ATTEMPTS = 8;

/* -------------------------------------------------------------------------- */
/*                                   Types                                    */
/* -------------------------------------------------------------------------- */

/**
 * POST /documents/upload/
 */
interface UploadDocumentResponse {
  id: number;
  status?: string;
  file_name?: string;
  source_type?: "docx" | "raw_text";
  created_at?: string;

  [key: string]: unknown;
}

/**
 * POST /documents/{documentId}/review/
 *
 * We intentionally keep this flexible because
 * the frontend only needs to know whether the
 * request itself succeeded.
 */
interface StartReviewResponse {
  success?: boolean;
  message?: string;

  review_job_id?: number;
  status?: string;

  [key: string]: unknown;
}

/**
 * Issue returned inside a document block.
 *
 * Some backend versions may contain extra fields,
 * so this interface remains extensible.
 */
interface BackendIssue {
  id?: number;

  issue_code?: string;

  title?: string;
  description?: string;

  severity?: string;

  /**
   * Legacy offsets.
   *
   * These fields are kept for compatibility with
   * the current blocks-with-issues response.
   */
  start_offset?: number;
  end_offset?: number;

  /**
   * Offsets based on normalized_text.
   *
   * The highlighting UI uses these offsets whenever
   * normalized_text is displayed.
   */
  normalized_start_offset?: number;
  normalized_end_offset?: number;

  /**
   * Offsets based on raw_text.
   *
   * These values are used only when the block has no
   * normalized_text and the UI falls back to raw_text.
   */
  raw_start_offset?: number;
  raw_end_offset?: number;

  original_segment?: string;
  normalized_original_segment?: string;
  raw_original_segment?: string;

  suggestion_text?: string;

  extra_data?: {
    original_segment?: string;
    normalized_original_segment?: string;
    raw_original_segment?: string;

    [key: string]: unknown;
  };

  [key: string]: unknown;
}

/**
 * GET /documents/{documentId}/blocks-with-issues/
 */
interface BackendBlock {
  id: number;
  document: number;

  parent_heading: number | null;

  block_type: string;
  heading_level: number | null;
  order_index: number;

  raw_text: string;
  normalized_text: string;

  style_name?: string;

  is_rtl: boolean;
  alignment: string;

  paragraph_index?: number | null;

  table_index?: number | null;
  row_index?: number | null;
  cell_index?: number | null;
  cell_paragraph_index?: number | null;

  format_metadata?: Record<string, unknown>;

  is_heading?: boolean;
  has_children?: boolean;

  issues_count: number;
  issues: BackendIssue[];

  created_at?: string;
  updated_at?: string;

  [key: string]: unknown;
}

/**
 * GET /documents/{documentId}/differences/
 */
interface BackendDifference {
  id: number;

  document_id: number;
  block_id: number;
  review_job: number | null;

  difference_type: string;
  change_kind: string;

  raw_phrase: string;
  normalized_phrase: string;

  raw_start_offset: number;
  raw_end_offset: number;

  normalized_start_offset: number;
  normalized_end_offset: number;

  context_data?: Record<string, unknown>;
  metadata?: Record<string, unknown>;

  created_at?: string;

  [key: string]: unknown;
}

interface PaginatedResponse<T> {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: T[];

  [key: string]: unknown;
}

/**
 * Newer export endpoint can return JSON metadata
 * containing a URL to the generated DOCX.
 */
interface ExportDocumentResponse {
  message?: string;

  document_id?: number;

  version?: number;

  download_url?: string;

  created_at?: string;

  [key: string]: unknown;
}

/**
 * API error preserving HTTP status and backend payload.
 */
class ApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(
    message: string,
    status: number,
    payload: unknown,
  ) {
    super(message);

    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

/* -------------------------------------------------------------------------- */
/*                                  Helpers                                   */
/* -------------------------------------------------------------------------- */

const wait = (duration: number): Promise<void> =>
  new Promise((resolve) => {
    window.setTimeout(resolve, duration);
  });

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

async function readResponsePayload(
  response: Response,
): Promise<unknown> {
  const text = await response.text();

  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function findErrorMessage(
  payload: unknown,
): string | null {
  if (
    typeof payload === "string" &&
    payload.trim()
  ) {
    return payload;
  }

  if (Array.isArray(payload)) {
    for (const value of payload) {
      const message =
        findErrorMessage(value);

      if (message) {
        return message;
      }
    }

    return null;
  }

  if (!isRecord(payload)) {
    return null;
  }

  const preferredKeys = [
    "detail",
    "error",
    "message",
    "document",
    "non_field_errors",
  ];

  for (const key of preferredKeys) {
    const message =
      findErrorMessage(payload[key]);

    if (message) {
      return message;
    }
  }

  for (const value of Object.values(payload)) {
    const message =
      findErrorMessage(value);

    if (message) {
      return message;
    }
  }

  return null;
}

async function createApiError(
  response: Response,
  fallbackMessage: string,
): Promise<ApiError> {
  const payload =
    await readResponsePayload(response);

  return new ApiError(
    findErrorMessage(payload) ??
      fallbackMessage,
    response.status,
    payload,
  );
}

/**
 * The backend currently returns HTTP 400 while
 * blocks are requested before parsing has finished.
 *
 * Example:
 *
 * {
 *   "document":
 *     "Blocks are not available until the document has been parsed.",
 *   "status": "uploaded"
 * }
 */
function isDocumentStillParsing(
  error: unknown,
): boolean {
  if (!(error instanceof ApiError)) {
    return false;
  }

  if (error.status !== 400) {
    return false;
  }

  if (isRecord(error.payload)) {
    const status =
      error.payload.status;

    if (
      status === "uploaded" ||
      status === "parsing"
    ) {
      return true;
    }
  }

  return error.message
    .toLowerCase()
    .includes(
      "blocks are not available until the document has been parsed",
    );
}

/**
 * Normalize blocks before using them in the UI.
 */
function sortBlocks(
  blocks: BackendBlock[],
): BackendBlock[] {
  return [...blocks].sort(
    (first, second) =>
      first.order_index -
      second.order_index,
  );
}

/**
 * Generates a lightweight signature of reviewed
 * document state.
 *
 * This is used because the current API contract
 * does not expose a review-status endpoint.
 */
function createBlocksSignature(
  blocks: BackendBlock[],
): string {
  return sortBlocks(blocks)
    .map((block) => {
      const issueCount =
        block.issues_count ??
        block.issues?.length ??
        0;

      return [
        block.id,
        block.normalized_text ?? "",
        issueCount,
      ].join(":");
    })
    .join("|");
}

/**
 * Detect whether the review has produced visible
 * review information.
 */
function blocksContainReviewData(
  blocks: BackendBlock[],
): boolean {
  return blocks.some((block) => {
    const issueCount =
      block.issues_count ??
      block.issues?.length ??
      0;

    if (issueCount > 0) {
      return true;
    }

    if (
      Array.isArray(block.issues) &&
      block.issues.length > 0
    ) {
      return true;
    }

    return (
      Boolean(block.normalized_text) &&
      block.normalized_text !==
        block.raw_text
    );
  });
}

function getDifferencePresentation(
  difference: BackendDifference,
): {
  issueCode: string;
  title: string;
  description: string;
  severity: string;
} {
  const {
    difference_type: differenceType,
    change_kind: changeKind,
    raw_phrase: rawPhrase,
    normalized_phrase: normalizedPhrase,
  } = difference;

  if (
    changeKind === "space_to_half_space"
  ) {
    return {
      issueCode: "half_space",
      title: "اصلاح نیم‌فاصله",
      description:
        "فاصله معمولی به نیم‌فاصله استاندارد فارسی تبدیل شده است.",
      severity: "warning",
    };
  }

  if (
    changeKind === "half_space_to_space"
  ) {
    return {
      issueCode: "spacing",
      title: "اصلاح فاصله",
      description:
        "نیم‌فاصله نامناسب به فاصله معمولی تبدیل شده است.",
      severity: "warning",
    };
  }

  if (
    differenceType === "whitespace_change"
  ) {
    return {
      issueCode: "spacing",
      title: "اصلاح فاصله‌گذاری",
      description:
        "فاصله‌گذاری متن برای بهبود نگارش اصلاح شده است.",
      severity: "warning",
    };
  }

  const punctuationPattern =
    /[.,،؛؟!?:«»()[\]{}]/u;

  if (
    punctuationPattern.test(rawPhrase) ||
    punctuationPattern.test(normalizedPhrase)
  ) {
    return {
      issueCode: "punctuation",
      title: "اصلاح علائم نگارشی",
      description:
        "جای‌گذاری یا فاصله‌گذاری علائم نگارشی اصلاح شده است.",
      severity: "warning",
    };
  }

  if (changeKind === "insertion") {
    return {
      issueCode: "suggestion",
      title: "افزودن عبارت",
      description:
        "برای بهبود متن، افزودن این عبارت پیشنهاد شده است.",
      severity: "info",
    };
  }

  if (changeKind === "deletion") {
    return {
      issueCode: "suggestion",
      title: "حذف عبارت",
      description:
        "برای بهبود متن، حذف این عبارت پیشنهاد شده است.",
      severity: "info",
    };
  }

  return {
    issueCode: "grammar",
    title: "اصلاح واژه یا عبارت",
    description:
      "واژه یا عبارت با شکل پیشنهادی جایگزین شده است.",
    severity: "warning",
  };
}

function mapDifferenceToIssue(
  difference: BackendDifference,
): BackendIssue {
  const presentation =
    getDifferencePresentation(
      difference,
    );

  return {
    id: difference.id,

    issue_code:
      presentation.issueCode,

    title:
      presentation.title,

    description:
      presentation.description,

    severity:
      presentation.severity,

    raw_start_offset:
      difference.raw_start_offset,

    raw_end_offset:
      difference.raw_end_offset,

    normalized_start_offset:
      difference.normalized_start_offset,

    normalized_end_offset:
      difference.normalized_end_offset,

    original_segment:
      difference.raw_phrase,

    raw_original_segment:
      difference.raw_phrase,

    normalized_original_segment:
      difference.normalized_phrase,

    suggestion_text:
      difference.normalized_phrase,

    extra_data: {
      original_segment:
        difference.raw_phrase,

      raw_original_segment:
        difference.raw_phrase,

      normalized_original_segment:
        difference.normalized_phrase,

      difference_type:
        difference.difference_type,

      change_kind:
        difference.change_kind,

      review_job:
        difference.review_job,

      context_data:
        difference.context_data ?? {},

      metadata:
        difference.metadata ?? {},
    },
  };
}

function attachDifferencesToBlocks(
  blocks: BackendBlock[],
  differences: BackendDifference[],
): BackendBlock[] {
  const differencesByBlock =
    new Map<number, BackendIssue[]>();

  for (const difference of differences) {
    const issue =
      mapDifferenceToIssue(
        difference,
      );

    const blockIssues =
      differencesByBlock.get(
        difference.block_id,
      ) ?? [];

    blockIssues.push(issue);

    differencesByBlock.set(
      difference.block_id,
      blockIssues,
    );
  }

  return blocks.map((block) => {
    const differenceIssues =
      differencesByBlock.get(block.id);

    if (
      !differenceIssues ||
      differenceIssues.length === 0
    ) {
      return block;
    }

    return {
      ...block,
      issues: differenceIssues,
      issues_count:
        differenceIssues.length,
    };
  });
}

/* -------------------------------------------------------------------------- */
/*                               API Endpoint 1                               */
/* -------------------------------------------------------------------------- */

/**
 * Upload DOCX
 *
 * POST
 * /api/v1/documents/upload/
 */
export async function uploadDocument(
  file: File,
): Promise<UploadDocumentResponse> {
  const formData = new FormData();

  /**
   * Backend expects multipart field:
   *
   * file
   */
  formData.append("file", file);

  const response = await fetch(
    `${API_BASE_URL}/documents/upload/`,
    {
      method: "POST",
      body: formData,
    },
  );

  if (!response.ok) {
    throw await createApiError(
      response,
      "آپلود فایل با خطا مواجه شد.",
    );
  }

  const data =
    (await response.json()) as UploadDocumentResponse;

  if (
    typeof data.id !== "number" ||
    !Number.isFinite(data.id)
  ) {
    throw new Error(
      "شناسه سند از Backend دریافت نشد.",
    );
  }

  return data;
}

/**
 * Upload raw text through the same document-ingestion endpoint.
 *
 * POST
 * /api/v1/documents/upload/
 *
 * The backend accepts exactly one source per request: either a DOCX file
 * as multipart/form-data or raw_text as JSON.
 */
export async function uploadRawText(
  rawText: string,
): Promise<UploadDocumentResponse> {
  const normalizedText = rawText.trim();

  if (!normalizedText) {
    throw new Error(
      "متنی برای پردازش وارد نشده است.",
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/documents/upload/`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        raw_text: normalizedText,
      }),
    },
  );

  if (!response.ok) {
    throw await createApiError(
      response,
      "ارسال متن به ویراستار با خطا مواجه شد.",
    );
  }

  const data =
    (await response.json()) as UploadDocumentResponse;

  if (
    typeof data.id !== "number" ||
    !Number.isFinite(data.id)
  ) {
    throw new Error(
      "شناسه سند از Backend دریافت نشد.",
    );
  }

  return data;
}

/* -------------------------------------------------------------------------- */
/*                               API Endpoint 2                               */
/* -------------------------------------------------------------------------- */

/**
 * Get all normalized blocks + issues
 *
 * GET
 * /api/v1/documents/{documentId}/blocks-with-issues/
 *
 * No query parameter.
 * No request body.
 */
export async function getDocumentBlocks(
  documentId: number,
): Promise<BackendBlock[]> {
  const response = await fetch(
    `${API_BASE_URL}/documents/${documentId}/blocks-with-issues/`,
    {
      method: "GET",
    },
  );

  if (!response.ok) {
    throw await createApiError(
      response,
      "دریافت متن و نتایج ویراستاری با خطا مواجه شد.",
    );
  }

  const data: unknown =
    await response.json();

  /**
   * Endpoint documentation says response is a list.
   */
  if (!Array.isArray(data)) {
    throw new Error(
      "ساختار پاسخ blocks-with-issues معتبر نیست.",
    );
  }

  return data as BackendBlock[];
}

/* -------------------------------------------------------------------------- */
/*                               API Endpoint 3                               */
/* -------------------------------------------------------------------------- */

/**
 * Start LLM review
 *
 * POST
 * /api/v1/documents/{documentId}/review/
 */
export async function startDocumentReview(
  documentId: number,
): Promise<StartReviewResponse> {
  const response = await fetch(
    `${API_BASE_URL}/documents/${documentId}/review/`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw await createApiError(
      response,
      "شروع فرایند ویراستاری با خطا مواجه شد.",
    );
  }

  /**
   * Some POST responses may be empty.
   */
  const payload =
    await readResponsePayload(response);

  if (isRecord(payload)) {
    return payload as StartReviewResponse;
  }

  return {
    success: true,
  };
}

/* -------------------------------------------------------------------------- */
/*                               API Endpoint 4                               */
/* -------------------------------------------------------------------------- */

/**
 * Get raw/normalized document differences.
 *
 * GET
 * /api/v1/documents/{documentId}/differences/
 *
 * Optional:
 * ?review_job_id={reviewJobId}
 */
export async function getDocumentDifferences(
  documentId: number,
  reviewJobId?: number,
): Promise<BackendDifference[]> {
  const url =
    new URL(
      `${API_BASE_URL}/documents/${documentId}/differences/`,
    );

  if (
    typeof reviewJobId === "number" &&
    Number.isInteger(reviewJobId) &&
    reviewJobId > 0
  ) {
    url.searchParams.set(
      "review_job_id",
      String(reviewJobId),
    );
  }

  const response = await fetch(
    url.toString(),
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw await createApiError(
      response,
      "دریافت تفاوت‌های متن با خطا مواجه شد.",
    );
  }

  const data: unknown =
    await response.json();

  if (Array.isArray(data)) {
    return data as BackendDifference[];
  }

  if (
    isRecord(data) &&
    Array.isArray(
      (
        data as PaginatedResponse<BackendDifference>
      ).results,
    )
  ) {
    return (
      data as PaginatedResponse<BackendDifference>
    ).results ?? [];
  }

  throw new Error(
    "ساختار پاسخ differences معتبر نیست.",
  );
}

/* -------------------------------------------------------------------------- */
/*                               API Endpoint 5                               */
/* -------------------------------------------------------------------------- */

/**
 * Export final DOCX
 *
 * GET
 * /api/v1/documents/{documentId}/export-docx/
 */
export async function downloadFinalDocument(
  documentId: number | string,
): Promise<void> {
  const numericDocumentId =
    Number(documentId);

  if (
    !Number.isInteger(
      numericDocumentId,
    ) ||
    numericDocumentId <= 0
  ) {
    throw new Error(
      "شناسه سند معتبر نیست.",
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/documents/${numericDocumentId}/export-docx/`,
    {
      method: "GET",
    },
  );

  if (!response.ok) {
    throw await createApiError(
      response,
      "تولید فایل Word نهایی با خطا مواجه شد.",
    );
  }

  const contentType =
    response.headers
      .get("content-type")
      ?.toLowerCase() ?? "";

  /**
   * Backend implementation may return:
   *
   * {
   *   download_url: "..."
   * }
   */
  if (
    contentType.includes(
      "application/json",
    )
  ) {
    const data =
      (await response.json()) as ExportDocumentResponse;

    if (!data.download_url) {
      throw new Error(
        "Backend آدرس فایل DOCX را برنگرداند.",
      );
    }

    const downloadUrl =
      new URL(
        data.download_url,
        response.url,
      ).toString();

    await downloadFileFromUrl(
      downloadUrl,
      `edited-document-${numericDocumentId}.docx`,
    );

    return;
  }

  /**
   * Backend may alternatively return the DOCX
   * binary directly.
   */
  const blob =
    await response.blob();

  downloadBlob(
    blob,
    `edited-document-${numericDocumentId}.docx`,
  );
}

/* -------------------------------------------------------------------------- */
/*                              Parsing Polling                               */
/* -------------------------------------------------------------------------- */

/**
 * Wait until the uploaded DOCX has been parsed.
 *
 * There is no separate document-status endpoint
 * in the current frontend API contract.
 *
 * Therefore:
 *
 * GET blocks
 *
 * 400 → parsing has not completed → retry
 * 200 → blocks available → parsed
 */
async function waitForParsedBlocks(
  documentId: number,
  maxAttempts = PARSING_MAX_ATTEMPTS,
): Promise<BackendBlock[]> {
  for (
    let attempt = 1;
    attempt <= maxAttempts;
    attempt += 1
  ) {
    try {
      const blocks =
        await getDocumentBlocks(
          documentId,
        );

      /**
       * A successfully parsed empty DOCX is unusual.
       *
       * For the current workflow we require
       * at least one block.
       */
      if (blocks.length > 0) {
        console.log(
          `Document ${documentId} parsed successfully.`,
        );

        return blocks;
      }

      console.debug(
        `Document ${documentId} has no blocks yet. Attempt ${attempt}/${maxAttempts}.`,
      );
    } catch (error) {
      if (
        !isDocumentStillParsing(error)
      ) {
        throw error;
      }

      console.debug(
        `Document ${documentId} is still parsing. Attempt ${attempt}/${maxAttempts}.`,
      );
    }

    await wait(
      PARSING_POLL_INTERVAL_MS,
    );
  }

  throw new Error(
    "پردازش اولیه فایل Word بیش از حد انتظار طول کشید.",
  );
}

/* -------------------------------------------------------------------------- */
/*                               Review‍ Polling                               */
/* -------------------------------------------------------------------------- */

/**
 * Current backend exposes no review-status endpoint
 * in the API contract provided to the frontend.
 *
 * Therefore blocks-with-issues is the only readable
 * endpoint that can reflect the result of the review.
 *
 * We compare its state before and after POST review.
 */
async function waitForReviewedBlocks(
  documentId: number,
  blocksBeforeReview: BackendBlock[],
  maxAttempts = REVIEW_MAX_ATTEMPTS,
): Promise<BackendBlock[]> {
  const initialSignature =
    createBlocksSignature(
      blocksBeforeReview,
    );

  const startedAt =
    Date.now();

  let latestBlocks =
    blocksBeforeReview;

  for (
    let attempt = 1;
    attempt <= maxAttempts;
    attempt += 1
  ) {
    await wait(
      REVIEW_POLL_INTERVAL_MS,
    );

    try {
      latestBlocks =
        await getDocumentBlocks(
          documentId,
        );
    } catch (error) {
      /**
       * Temporary errors are tolerated while
       * background processing is happening.
       */
      if (
        error instanceof ApiError &&
        (
          error.status === 400 ||
          error.status === 409
        )
      ) {
        console.debug(
          `Review for document ${documentId} is still running. Attempt ${attempt}/${maxAttempts}.`,
        );

        continue;
      }

      throw error;
    }

    const elapsed =
      Date.now() - startedAt;

    /**
     * Do not accept the immediate first response,
     * because POST /review may queue asynchronous work.
     */
    if (
      elapsed <
      REVIEW_MIN_WAIT_MS
    ) {
      continue;
    }

    const currentSignature =
      createBlocksSignature(
        latestBlocks,
      );

    /**
     * The safest signal available with the
     * current API endpoints:
     *
     * - block content changed
     * - issue counts changed
     * - issues appeared
     */
    if (
      currentSignature !==
        initialSignature ||
      blocksContainReviewData(
        latestBlocks,
      )
    ) {
      console.log(
        `Review result detected for document ${documentId}.`,
      );

      return latestBlocks;
    }

    console.debug(
      `Waiting for review result for document ${documentId}. Attempt ${attempt}/${maxAttempts}.`,
    );
  }

  /**
   * IMPORTANT:
   *
   * A correct document may legitimately have zero
   * issues, so unchanged blocks do NOT necessarily
   * mean that review failed.
   *
   * Since the current backend exposes no status API,
   * return the latest successful blocks response
   * instead of falsely reporting a failure.
   */
  console.warn(
    `Could not determine review completion explicitly for document ${documentId}. Using the latest blocks response.`,
  );

  return latestBlocks;
}

/**
 * Wait briefly for the asynchronous block-difference
 * task that runs after document review.
 *
 * A document may legitimately have no differences.
 * Therefore this helper returns the latest successful
 * empty response after a short polling window instead
 * of treating it as an error.
 */
async function waitForDocumentDifferences(
  documentId: number,
  reviewJobId?: number,
  maxAttempts = DIFFERENCES_MAX_ATTEMPTS,
): Promise<BackendDifference[]> {
  let latestDifferences:
    BackendDifference[] = [];

  for (
    let attempt = 1;
    attempt <= maxAttempts;
    attempt += 1
  ) {
    try {
      latestDifferences =
        await getDocumentDifferences(
          documentId,
          reviewJobId,
        );

      if (latestDifferences.length > 0) {
        console.log(
          `Differences received for document ${documentId}.`,
        );

        return latestDifferences;
      }
    } catch (error) {
      if (
        error instanceof ApiError &&
        (
          error.status === 400 ||
          error.status === 404 ||
          error.status === 409
        )
      ) {
        console.debug(
          `Differences for document ${documentId} are not ready yet. Attempt ${attempt}/${maxAttempts}.`,
        );
      } else {
        throw error;
      }
    }

    if (attempt < maxAttempts) {
      await wait(
        DIFFERENCES_POLL_INTERVAL_MS,
      );
    }
  }

  console.warn(
    `No stored differences were returned for document ${documentId}. Existing block issues will be used as fallback.`,
  );

  return latestDifferences;
}

/* -------------------------------------------------------------------------- */
/*                              Editor Mapping                                */
/* -------------------------------------------------------------------------- */

function getIssueSearchText(
  issue: unknown,
): string {
  try {
    return JSON.stringify(
      issue,
    ).toLowerCase();
  } catch {
    return "";
  }
}

type IssueOffsetBasis =
  | "normalized"
  | "raw";

interface IssueOffsetRange {
  startOffset: number;
  endOffset: number;
}

/**
 * Maps backend issue metadata to the visual
 * category used by the editor highlights.
 */
function getIssueCategory(
  issue: BackendIssue,
): EditorIssue["category"] {
  const searchableText =
    getIssueSearchText(issue);

  if (
    searchableText.includes(
      "half_space",
    ) ||
    searchableText.includes(
      "half-space",
    ) ||
    searchableText.includes(
      "halfspace",
    ) ||
    searchableText.includes(
      "نیم‌فاصله",
    ) ||
    searchableText.includes(
      "نیم فاصله",
    )
  ) {
    return "half-space";
  }

  if (
    searchableText.includes(
      "spacing",
    ) ||
    searchableText.includes(
      "فاصله‌گذاری",
    ) ||
    searchableText.includes(
      "فاصله گذاری",
    )
  ) {
    return "spacing";
  }

  if (
    searchableText.includes(
      "punctuation",
    ) ||
    searchableText.includes(
      "نشانه‌گذاری",
    ) ||
    searchableText.includes(
      "نشانه گذاری",
    ) ||
    searchableText.includes(
      "علائم نگارشی",
    )
  ) {
    return "punctuation";
  }

  if (
    searchableText.includes(
      "consistency",
    ) ||
    searchableText.includes(
      "uniform",
    ) ||
    searchableText.includes(
      "style",
    ) ||
    searchableText.includes(
      "یکدست",
    )
  ) {
    return "consistency";
  }

  if (
    searchableText.includes(
      "grammar",
    ) ||
    searchableText.includes(
      "spelling",
    ) ||
    searchableText.includes(
      "املایی",
    ) ||
    searchableText.includes(
      "دستوری",
    ) ||
    searchableText.includes(
      "نگارشی",
    )
  ) {
    return "grammar";
  }

  return "suggestion";
}

/**
 * Resolve issue offsets against the exact text
 * currently rendered by the editor.
 *
 * normalized_text:
 * normalized_start_offset / normalized_end_offset
 *
 * raw_text:
 * raw_start_offset / raw_end_offset
 *
 * start_offset / end_offset remain as a temporary
 * compatibility fallback for the current API.
 */
function getIssueOffsetRange(
  issue: BackendIssue,
  basis: IssueOffsetBasis,
): IssueOffsetRange | null {
  const startOffset =
    basis === "normalized"
      ? (
          issue.normalized_start_offset ??
          issue.start_offset
        )
      : (
          issue.raw_start_offset ??
          issue.start_offset
        );

  const endOffset =
    basis === "normalized"
      ? (
          issue.normalized_end_offset ??
          issue.end_offset
        )
      : (
          issue.raw_end_offset ??
          issue.end_offset
        );

  if (
    typeof startOffset !== "number" ||
    typeof endOffset !== "number" ||
    !Number.isInteger(startOffset) ||
    !Number.isInteger(endOffset) ||
    startOffset < 0 ||
    endOffset <= startOffset
  ) {
    return null;
  }

  return {
    startOffset,
    endOffset,
  };
}


function createMetrics(
  blocks: BackendBlock[],
) {
  let grammar = 0;
  let halfSpace = 0;
  let consistency = 0;
  let suggestions = 0;

  let classifiedIssues = 0;

  for (const block of blocks) {
    for (
      const issue of
      block.issues ?? []
    ) {
      const issueText =
        getIssueSearchText(issue);

      /**
       * Half-space
       */
      if (
        issueText.includes(
          "half_space",
        ) ||
        issueText.includes(
          "half-space",
        ) ||
        issueText.includes(
          "halfspace",
        ) ||
        issueText.includes(
          "نیم‌فاصله",
        ) ||
        issueText.includes(
          "نیم فاصله",
        )
      ) {
        halfSpace += 1;
        classifiedIssues += 1;

        continue;
      }

      /**
       * Grammar / spelling / punctuation
       */
      if (
        issueText.includes(
          "grammar",
        ) ||
        issueText.includes(
          "spelling",
        ) ||
        issueText.includes(
          "punctuation",
        ) ||
        issueText.includes(
          "نگارش",
        ) ||
        issueText.includes(
          "املایی",
        ) ||
        issueText.includes(
          "دستور",
        )
      ) {
        grammar += 1;
        classifiedIssues += 1;

        continue;
      }

      /**
       * Consistency / style
       */
      if (
        issueText.includes(
          "consistency",
        ) ||
        issueText.includes(
          "uniform",
        ) ||
        issueText.includes(
          "style",
        ) ||
        issueText.includes(
          "یکدست",
        )
      ) {
        consistency += 1;
        classifiedIssues += 1;

        continue;
      }

      /**
       * Suggestions
       */
      if (
        issueText.includes(
          "suggestion",
        ) ||
        issueText.includes(
          "recommendation",
        ) ||
        issueText.includes(
          "پیشنهاد",
        ) ||
        issueText.includes(
          "optimization",
        )
      ) {
        suggestions += 1;
        classifiedIssues += 1;

        continue;
      }

      /**
       * Unknown issue type
       */
      suggestions += 1;
      classifiedIssues += 1;
    }
  }

  /**
   * Backend might provide issues_count even if
   * issue details are incomplete.
   */
  const backendIssueCount =
    blocks.reduce(
      (total, block) =>
        total +
        (
          block.issues_count ??
          0
        ),
      0,
    );

  const missingIssueDetails =
    Math.max(
      backendIssueCount -
        classifiedIssues,
      0,
    );

  suggestions +=
    missingIssueDetails;

  return {
    grammar,
    halfSpace,
    consistency,
    suggestions,
  };
}

function getBlockTextSource(
  block: BackendBlock,
): {
  text: string;
  basis: IssueOffsetBasis;
} {
  if (
    typeof block.normalized_text ===
      "string" &&
    block.normalized_text.length > 0
  ) {
    return {
      text: block.normalized_text,
      basis: "normalized",
    };
  }

  return {
    text: block.raw_text ?? "",
    basis: "raw",
  };
}

function getBlockText(
  block: BackendBlock,
): string {
  return getBlockTextSource(
    block,
  ).text;
}

function createEditedText(
  blocks: BackendBlock[],
): string {
  return [...blocks]
    .sort(
      (first, second) =>
        first.order_index -
        second.order_index,
    )
    .map((block) =>
      getBlockText(block).trim(),
    )
    .filter(Boolean)
    .join("\n\n");
}

function escapeHtml(
  value: string,
): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderTextWithIssues(
  text: string,
  issues: BackendIssue[],
  basis: IssueOffsetBasis,
): string {
  const validIssues = issues
    .map((issue) => ({
      issue,
      range:
        getIssueOffsetRange(
          issue,
          basis,
        ),
    }))
    .filter(
      (
        item,
      ): item is {
        issue: BackendIssue;
        range: IssueOffsetRange;
      } => {
        const { range } = item;

        return (
          range !== null &&
          range.endOffset <=
            text.length
        );
      },
    )
    .sort(
      (first, second) =>
        first.range.startOffset -
        second.range.startOffset,
    );

  if (validIssues.length === 0) {
    return escapeHtml(text);
  }

  const htmlParts: string[] = [];
  let currentOffset = 0;

  for (
    const {
      issue,
      range,
    } of validIssues
  ) {
    const {
      startOffset,
      endOffset,
    } = range;

    /*
     * فعلاً Issueهای Overlap شده را نادیده می‌گیریم.
     */
    if (
      startOffset <
      currentOffset
    ) {
      continue;
    }

    htmlParts.push(
      escapeHtml(
        text.slice(
          currentOffset,
          startOffset,
        ),
      ),
    );

    const category =
      getIssueCategory(issue);

    const issueTitle =
      issue.title ||
      "پیشنهاد اصلاحی";

    const suggestion =
      issue.suggestion_text || "";

    const tooltip = suggestion
      ? `${issueTitle} — پیشنهاد: ${suggestion}`
      : issueTitle;

    htmlParts.push(
      `<span ` +
        `class="editor-issue-highlight" ` +
        `data-issue-category="${category}" ` +
        `data-issue-title="${escapeHtml(issueTitle)}" ` +
        `data-offset-basis="${basis}" ` +
        `title="${escapeHtml(tooltip)}">` +
        `${escapeHtml(
          text.slice(
            startOffset,
            endOffset,
          ),
        )}` +
        `</span>`,
    );

    currentOffset =
      endOffset;
  }

  htmlParts.push(
    escapeHtml(
      text.slice(currentOffset),
    ),
  );

  return htmlParts.join("");
}

function normalizeAlignment(
  alignment: string,
  isRtl: boolean,
): "left" | "right" | "center" | "justify" {
  switch (alignment?.toLowerCase()) {
    case "left":
      return "left";

    case "right":
      return "right";

    case "center":
      return "center";

    case "justify":
    case "both":
      return "justify";

    default:
      return isRtl
        ? "right"
        : "left";
  }
}

function renderNormalBlock(
  block: BackendBlock,
): string {
  const {
    text,
    basis,
  } = getBlockTextSource(block);

  if (!text.trim()) {
    return "";
  }

  const direction =
    block.is_rtl
      ? "rtl"
      : "ltr";

  const alignment =
    normalizeAlignment(
      block.alignment,
      block.is_rtl,
    );

  const style =
    `direction:${direction};` +
    `text-align:${alignment};`;

  /*
   * متن را همراه با Issueهای همان Block
   * به HTML هایلایت‌شده تبدیل می‌کنیم.
   */
  const renderedText =
    renderTextWithIssues(
      text,
      block.issues ?? [],
      basis,
    );

  const isHeading =
    block.is_heading === true ||
    block.block_type === "heading";

  if (isHeading) {
    const level = Math.min(
      Math.max(
        block.heading_level ?? 1,
        1,
      ),
      6,
    );

    return (
      `<h${level} dir="${direction}" style="${style}">` +
      `${renderedText}` +
      `</h${level}>`
    );
  }

  return (
    `<p dir="${direction}" style="${style}">` +
    `${renderedText}` +
    `</p>`
  );
}

function renderTable(
  tableBlocks: BackendBlock[],
): string {
  const rows = new Map<
    number,
    Map<number, BackendBlock[]>
  >();

  for (const block of tableBlocks) {
    const rowIndex =
      block.row_index ?? 0;

    const cellIndex =
      block.cell_index ?? 0;

    if (!rows.has(rowIndex)) {
      rows.set(
        rowIndex,
        new Map(),
      );
    }

    const row =
      rows.get(rowIndex)!;

    if (!row.has(cellIndex)) {
      row.set(
        cellIndex,
        [],
      );
    }

    row.get(cellIndex)!.push(
      block,
    );
  }

  const renderedRows =
    [...rows.entries()]
      .sort(
        ([first], [second]) =>
          first - second,
      )
      .map(([, cells]) => {
        const renderedCells =
          [...cells.entries()]
            .sort(
              ([first], [second]) =>
                first - second,
            )
            .map(([, cellBlocks]) => {
              const content =
                [...cellBlocks]
                  .sort(
                    (first, second) =>
                      (
                        first.cell_paragraph_index ??
                        0
                      ) -
                      (
                        second.cell_paragraph_index ??
                        0
                      ),
                  )
                  .map((block) => {
                    const {
                      text,
                      basis,
                    } =
                      getBlockTextSource(
                        block,
                      );

                    if (!text.trim()) {
                      return "";
                    }

                    const direction =
                      block.is_rtl
                        ? "rtl"
                        : "ltr";

                    const alignment =
                      normalizeAlignment(
                        block.alignment,
                        block.is_rtl,
                      );

                    /*
                     * متن داخل هر سلول همراه با Issueهای
                     * همان Block رندر می‌شود.
                     */
                    const renderedText =
                      renderTextWithIssues(
                        text,
                        block.issues ?? [],
                        basis,
                      );

                    return (
                      `<p dir="${direction}" ` +
                      `style="direction:${direction};` +
                      `text-align:${alignment};">` +
                      `${renderedText}` +
                      `</p>`
                    );
                  })
                  .filter(Boolean)
                  .join("");

              return (
                `<td>${content}</td>`
              );
            })
            .join("");

        return (
          `<tr>${renderedCells}</tr>`
        );
      })
      .join("");

  return (
    `<div class="editor-table-wrapper">` +
    `<table><tbody>` +
    `${renderedRows}` +
    `</tbody></table>` +
    `</div>`
  );
}

function createEditedHtml(
  blocks: BackendBlock[],
): string {
  const sortedBlocks =
    [...blocks].sort(
      (first, second) =>
        first.order_index -
        second.order_index,
    );

  const renderedTables =
    new Set<number>();

  const htmlParts: string[] =
    [];

  for (const block of sortedBlocks) {
    if (
      typeof block.table_index ===
      "number"
    ) {
      const tableIndex =
        block.table_index;

      if (
        renderedTables.has(
          tableIndex,
        )
      ) {
        continue;
      }

      renderedTables.add(
        tableIndex,
      );

      const tableBlocks =
        sortedBlocks.filter(
          (candidate) =>
            candidate.table_index ===
            tableIndex,
        );

      htmlParts.push(
        renderTable(tableBlocks),
      );

      continue;
    }

    htmlParts.push(
      renderNormalBlock(block),
    );
  }

  return htmlParts
    .filter(Boolean)
    .join("");
}

function createEditorIssues(
  blocks: BackendBlock[],
): EditorIssue[] {
  return blocks.flatMap((block) =>
    (block.issues ?? []).map(
      (issue) => {
        const normalizedRange =
          getIssueOffsetRange(
            issue,
            "normalized",
          );

        const rawRange =
          getIssueOffsetRange(
            issue,
            "raw",
          );

        const preferredRange =
          normalizedRange ??
          rawRange;

        return {
          id: issue.id,

          issueCode:
            issue.issue_code ??
            "suggestion",

          category:
            getIssueCategory(issue),

          title:
            issue.title ??
            "پیشنهاد اصلاحی",

          description:
            issue.description ?? "",

          severity:
            issue.severity ?? "info",

          /*
           * EditorIssue currently exposes one pair
           * of offsets. Prefer normalized offsets
           * because normalized_text is the main
           * editor display source.
           */
          startOffset:
            preferredRange
              ?.startOffset ?? 0,

          endOffset:
            preferredRange
              ?.endOffset ?? 0,

          originalSegment:
            issue
              .normalized_original_segment ??
            issue.original_segment ??
            issue.extra_data
              ?.normalized_original_segment ??
            issue.extra_data
              ?.original_segment ??
            issue.raw_original_segment ??
            issue.extra_data
              ?.raw_original_segment ??
            "",

          suggestionText:
            issue.suggestion_text ?? "",
        };
      },
    ),
  );
}

function createEditorResult(
  documentId: number,
  blocks: BackendBlock[],
): EditorResult {
  return {
    documentId:
      String(documentId),

    metrics:
      createMetrics(blocks),

    editedText:
      createEditedText(blocks),

    editedHtml:
      createEditedHtml(blocks),

    issues:
      createEditorIssues(blocks),

    processedAt:
      new Date().toISOString(),
  };
}

/* -------------------------------------------------------------------------- */
/*                                  Download                                  */
/* -------------------------------------------------------------------------- */

function downloadBlob(
  blob: Blob,
  filename: string,
): void {
  const url =
    URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(
    link,
  );

  link.click();

  link.remove();

  window.setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 1000);
}

async function downloadFileFromUrl(
  url: string,
  filename: string,
): Promise<void> {
  const response =
    await fetch(url);

  if (!response.ok) {
    throw await createApiError(
      response,
      "دانلود فایل Word با خطا مواجه شد.",
    );
  }

  const blob =
    await response.blob();

  downloadBlob(
    blob,
    filename,
  );
}

/* -------------------------------------------------------------------------- */
/*                              Complete Pipeline                             */
/* -------------------------------------------------------------------------- */

/**
 * Complete document editing pipeline.
 *
 * The current backend endpoints used by this
 * workflow are:
 *
 * 1. POST upload
 * 2. GET blocks-with-issues
 * 3. POST review
 * 4. GET differences
 * 5. GET export-docx
 */
async function processDocument(
  source:
    | { type: "docx"; file: File }
    | { type: "raw_text"; text: string },
): Promise<EditorResult> {
  /**
   * STEP 1
   *
   * Upload the selected input source. Both DOCX and raw text use the same
   * backend document pipeline after ingestion.
   */
  const uploadedDocument =
    source.type === "docx"
      ? await uploadDocument(source.file)
      : await uploadRawText(source.text);

  const documentId =
    uploadedDocument.id;

  console.log(
    "Document uploaded:",
    documentId,
  );

  /**
   * STEP 2
   *
   * Upload starts backend parsing asynchronously.
   *
   * Wait until blocks become available.
   */
  const parsedBlocks =
    await waitForParsedBlocks(
      documentId,
    );

  console.log(
    "Document parsed:",
    documentId,
    "blocks:",
    parsedBlocks.length,
  );

  /**
   * STEP 3
   *
   * Document is parsed.
   * Start LLM review.
   */
  const reviewResponse =
    await startDocumentReview(
      documentId,
    );

  console.log(
    "Review started:",
    reviewResponse,
  );

  /**
   * STEP 4
   *
   * No review-status endpoint exists in the
   * current API contract.
   *
   * Therefore watch blocks-with-issues for
   * review results.
   */
  const reviewedBlocks =
    await waitForReviewedBlocks(
      documentId,
      parsedBlocks,
    );

  console.log(
    "Reviewed blocks received:",
    reviewedBlocks.length,
  );

  /**
   * STEP 5
   *
   * Review queues a separate asynchronous task
   * for generating raw/normalized differences.
   *
   * Fetch those differences using the review job
   * returned by POST /review.
   */
  const differences =
    await waitForDocumentDifferences(
      documentId,
      reviewResponse.review_job_id,
    );

  console.log(
    "Document differences received:",
    differences.length,
  );

  /**
   * Prefer the dedicated differences endpoint for
   * precise raw and normalized offsets.
   *
   * Blocks without stored differences keep their
   * existing issues as a compatibility fallback.
   */
  const blocksWithDifferences =
    attachDifferencesToBlocks(
      reviewedBlocks,
      differences,
    );

  /**
   * STEP 6
   *
   * Convert Backend result to the model
   * expected by the Editor UI.
   */
  return createEditorResult(
    documentId,
    blocksWithDifferences,
  );
}

/* -------------------------------------------------------------------------- */
/*                               Public Methods                               */
/* -------------------------------------------------------------------------- */

/**
 * Process uploaded DOCX.
 */
export async function processEditorFile(
  file: File,
): Promise<EditorResult> {
  if (!file) {
    throw new Error(
      "فایلی برای پردازش انتخاب نشده است.",
    );
  }

  const fileName =
    file.name.toLowerCase();

  if (
    !fileName.endsWith(".docx")
  ) {
    throw new Error(
      "در حال حاضر فقط فایل DOCX برای پردازش پشتیبانی می‌شود.",
    );
  }

  return processDocument({
    type: "docx",
    file,
  });
}

/**
 * Process text entered directly in the editor.
 */
export async function processEditorText(
  text: string,
): Promise<EditorResult> {
  if (!text.trim()) {
    throw new Error(
      "متنی برای پردازش وارد نشده است.",
    );
  }

  return processDocument({
    type: "raw_text",
    text,
  });
}
