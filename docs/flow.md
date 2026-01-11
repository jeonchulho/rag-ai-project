# 서비스 전체 플로우 다이어그램

아래는 RAG 기반 PDF 요약 및 자동 이메일 발송 워크플로우의 전체 흐름을 나타내는 Mermaid 다이어그램입니다.

```mermaid
graph TD
    subgraph 문서업로드/인덱싱
        A[Client\n자연어 명령 요청] --> B[upload/document\nPDF 업로드]
        B --> C[Document Ingestion\n텍스트 추출+청킹]
        C --> D[Vector Store\n임베딩 DB 저장]
    end

    subgraph 워크플로우
        E[Client\n자연어 명령\n(aaa.PDF 내용을 요약해서\n전철호에게 10시에 메일 보내줘)] --> F[search_agent.py]
        F --> G[Analyze Intent\n(llm_service.summarize, Entities)]
        G --> H[Extract Entities\n메일/시간/키워드 추출]
        H --> I[Vector Search\nPDF 문서 인덱스에서\n관련 청크 찾기]
        I --> J[Summarize Results\nllm_service.summarize(청크)]
        J --> K[Schedule Action\nworkers/tasks.py:send_email_task]
        K --> L[Task Queue\nCelery/Mail 발송 예약]
    end
```

---

## 단계별 설명

1. 문서 업로드: 사용자가 PDF 파일을 업로드합니다. 시스템은 문서에서 텍스트를 추출하고 청크 단위로 분할한 후 임베딩 DB에 저장합니다.
2. 자연어 명령 처리: 사용자가 자연어로 복합 명령을 입력합니다. (예: aaa.PDF 내용을 요약해서 전철호에게 10시에 메일 보내줘)
3. AI 에이전트 분석: 에이전트가 의도와 엔티티(메일 주소, 시간 등)를 추출합니다.
4. 검색 및 요약: PDF 인덱스에서 관련 내용을 벡터 검색, 필요한 부분을 요약합니다.
5. 액션 스케줄링: 작업 예약(이메일 발송 등), 백그라운드 워커(Celery)에 전달하여 실제 액션을 실행합니다.