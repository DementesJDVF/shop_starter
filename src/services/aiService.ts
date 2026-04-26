import api from '../utils/axios';

/**
 * Send a request to generate AI description
 * @param payload FormData (with image_file) or object (with image_url)
 * @returns task_id for polling
 */
export async function suggestDescription(
  payload: FormData | { image_url: string; product_id?: string }
): Promise<string> {
  const isFormData = payload instanceof FormData;
  const response = await api.post('products/suggest_description/', payload, {
    headers: isFormData ? { 'Content-Type': 'multipart/form-data' } : {},
  });
  return response.data.task_id;
}

/**
 * Poll the task status until completion or timeout
 * @param taskId The Celery task ID
 * @param maxAttempts Maximum polling attempts (default 30 = ~90 seconds)
 * @param intervalMs Interval between polls in milliseconds (default 3000 = 3 seconds)
 * @returns The generated description when task completes
 */
export async function pollTaskStatus(
  taskId: string,
  maxAttempts = 30,
  intervalMs = 3000
): Promise<string> {
  let attempts = 0;

  while (attempts < maxAttempts) {
    const response = await api.get(`products/tasks/${taskId}/`);
    const { status, result, error } = response.data;

    if (status === 'DONE') {
      return result;
    }

    if (status === 'FAILED') {
      throw new Error(error || 'Task failed');
    }

    // Wait before next attempt
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
    attempts++;
  }

  throw new Error('Timeout: La tarea tardó demasiado en completarse');
}

/**
 * Complete flow: send request and poll until result
 * @param payload FormData or object with image data
 * @returns The generated AI description
 */
export async function generateAIDescription(
  payload: FormData | { image_url: string; product_id?: string }
): Promise<string> {
  const taskId = await suggestDescription(payload);
  return await pollTaskStatus(taskId);
}
