/**
 * ============ CONFIG ============
 * Propriedades do Script: GEMINI_API_KEY, FOLDER_ID, OUTPUT_FOLDER_ID
 * SERVIÇO ATIVO: Drive API (v3)
 *
 * INSTRUÇÕES DE USO:
 * 1. Execute "inicializarSistema()" uma vez para configurar
 * 2. Configure um trigger para "processarProximoDaFila" a cada 5-10 minutos
 * 3. Execute "enfileirarAudios()" manualmente ou via trigger diário
 * ================================= */

function getCfg() {
  const props = PropertiesService.getScriptProperties();
  return {
    FOLDER_ID: props.getProperty('FOLDER_ID') || '',
    OUTPUT_FOLDER_ID: props.getProperty('OUTPUT_FOLDER_ID') || '',
    GEMINI_KEY: props.getProperty('GEMINI_API_KEY') || '',
    GEMINI_MODEL: 'gemini-2.5-flash',
    TIMEZONE: 'America/Sao_Paulo',
    MAX_POLLING_TENTATIVAS: 30,
    POLLING_INTERVALO_MS: 5000
  };
}

// ============ GERENCIAMENTO DE FILA ============

function getFilaKey() {
  return 'FILA_AUDIOS_V2';
}

function getEstadoKey() {
  return 'ESTADO_PROCESSAMENTO';
}

function obterFila() {
  const props = PropertiesService.getScriptProperties();
  const filaStr = props.getProperty(getFilaKey());
  return filaStr ? JSON.parse(filaStr) : [];
}

function salvarFila(fila) {
  PropertiesService.getScriptProperties().setProperty(getFilaKey(), JSON.stringify(fila));
}

function obterEstado() {
  const props = PropertiesService.getScriptProperties();
  const estadoStr = props.getProperty(getEstadoKey());
  return estadoStr ? JSON.parse(estadoStr) : null;
}

function salvarEstado(estado) {
  PropertiesService.getScriptProperties().setProperty(getEstadoKey(), JSON.stringify(estado));
}

function limparEstado() {
  PropertiesService.getScriptProperties().deleteProperty(getEstadoKey());
}

// ============ FUNÇÕES PRINCIPAIS ============

function inicializarSistema() {
  Logger.log('🔧 Inicializando sistema de transcrição...');

  const CFG = getCfg();

  if (!CFG.GEMINI_KEY) {
    Logger.log('❌ ERRO: GEMINI_API_KEY não configurada nas Propriedades do Script');
    return false;
  }

  if (!CFG.FOLDER_ID) {
    Logger.log('❌ ERRO: FOLDER_ID não configurado nas Propriedades do Script');
    return false;
  }

  limparEstado();
  salvarFila([]);

  Logger.log('✅ Sistema inicializado com sucesso!');
  Logger.log('📋 Próximos passos:');
  Logger.log('   1. Execute "enfileirarAudios()" para adicionar áudios à fila');
  Logger.log('   2. Configure um trigger para "processarProximoDaFila" a cada 5-10 min');

  return true;
}

function enfileirarAudios() {
  const CFG = getCfg();

  if (!CFG.FOLDER_ID) {
    Logger.log('❌ ERRO: FOLDER_ID não configurado');
    return;
  }

  Logger.log('🔍 Escaneando pasta por novos áudios...');

  const folder = DriveApp.getFolderById(CFG.FOLDER_ID);
  const files = folder.getFiles();
  const filaAtual = obterFila();
  const idsNaFila = new Set(filaAtual.map(item => item.fileId));

  let novosAudios = 0;

  while (files.hasNext()) {
    const file = files.next();
    const fileId = file.getId();
    const name = file.getName();
    const desc = file.getDescription() || '';
    const mime = file.getMimeType();

    if (desc.includes('processado')) continue;
    if (idsNaFila.has(fileId)) continue;

    const isAudio = mime.startsWith('audio/') || /\.(m4a|mp3|wav|aac|ogg)$/i.test(name);
    if (!isAudio) continue;

    filaAtual.push({
      fileId: fileId,
      fileName: name,
      mimeType: mime,
      fileSize: file.getSize(),
      adicionadoEm: new Date().toISOString()
    });

    novosAudios++;
    Logger.log(`   ➕ Adicionado: ${name}`);
  }

  salvarFila(filaAtual);
  Logger.log(`📋 Fila atualizada: ${novosAudios} novos áudios, ${filaAtual.length} total na fila`);
}

function processarProximoDaFila() {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(1000);
  } catch (e) {
    Logger.log('⚠️ Outra execução em andamento. Saindo.');
    return;
  }

  try {
    const estadoAnterior = obterEstado();

    if (estadoAnterior && estadoAnterior.etapa !== 'concluido') {
      Logger.log(`🔄 Retomando processamento de: ${estadoAnterior.fileName}`);
      continuarProcessamento(estadoAnterior);
      return;
    }

    const fila = obterFila();

    if (fila.length === 0) {
      Logger.log('✅ Fila vazia. Nenhum áudio para processar.');
      return;
    }

    const proximo = fila.shift();
    salvarFila(fila);

    Logger.log(`🎯 Processando: ${proximo.fileName} (${fila.length} restantes na fila)`);

    processarArquivo(proximo);

  } catch (err) {
    Logger.log(`❌ ERRO: ${err.message}`);
    Logger.log(`Stack: ${err.stack}`);
  } finally {
    lock.releaseLock();
  }
}

function processarArquivo(audioInfo) {
  const CFG = getCfg();

  try {
    const file = DriveApp.getFileById(audioInfo.fileId);

    const estado = {
      fileId: audioInfo.fileId,
      fileName: audioInfo.fileName,
      mimeType: audioInfo.mimeType,
      fileSize: audioInfo.fileSize,
      etapa: 'upload',
      iniciadoEm: new Date().toISOString()
    };
    salvarEstado(estado);

    Logger.log('📤 Etapa 1/4: Iniciando upload para Gemini...');
    const uploadResult = iniciarUpload(audioInfo);

    estado.etapa = 'upload_chunks';
    estado.uploadUrl = uploadResult.uploadUrl;
    estado.uploadOffset = 0;
    salvarEstado(estado);

    Logger.log('📤 Etapa 2/4: Enviando chunks...');
    const fileInfo = enviarChunks(estado);

    estado.etapa = 'aguardando_processamento';
    estado.fileServerName = fileInfo.file.name;
    estado.fileUri = fileInfo.file.uri;
    salvarEstado(estado);

    Logger.log('⏳ Etapa 3/4: Aguardando processamento do Google...');
    aguardarProcessamento(estado);

    estado.etapa = 'transcrevendo';
    salvarEstado(estado);

    Logger.log('🎙️ Etapa 4/4: Gerando transcrição...');
    const transcricao = gerarTranscricao(estado);

    if (transcricao && transcricao.length > 10) {
      const tema = extrairTema(transcricao);
      const docUrl = criarDocumentoTranscricao(audioInfo.fileName, tema, transcricao);

      file.setDescription((file.getDescription() || '') + ' | processado');

      const folder = DriveApp.getFolderById(CFG.FOLDER_ID);
      const subpastaProcessados = obterOuCriarSubpasta(folder, 'processados');
      moverParaSubpasta(file, folder, subpastaProcessados);

      Logger.log(`🎉 SUCESSO! Documento: ${docUrl}`);
    } else {
      Logger.log('⚠️ Transcrição vazia ou muito curta');
    }

    limparArquivoGemini(estado.fileServerName);

    estado.etapa = 'concluido';
    salvarEstado(estado);
    limparEstado();

  } catch (err) {
    Logger.log(`❌ Erro ao processar ${audioInfo.fileName}: ${err.message}`);

    const estado = obterEstado();
    if (estado) {
      estado.erro = err.message;
      estado.tentativas = (estado.tentativas || 0) + 1;

      if (estado.tentativas >= 3) {
        Logger.log('❌ Máximo de tentativas atingido. Removendo da fila.');
        limparEstado();
      } else {
        salvarEstado(estado);
      }
    }
  }
}

function continuarProcessamento(estado) {
  const CFG = getCfg();

  try {
    switch (estado.etapa) {
      case 'upload':
      case 'upload_chunks':
        Logger.log('🔄 Reiniciando upload do início...');
        processarArquivo({
          fileId: estado.fileId,
          fileName: estado.fileName,
          mimeType: estado.mimeType,
          fileSize: estado.fileSize
        });
        break;

      case 'aguardando_processamento':
        Logger.log('🔄 Continuando a aguardar processamento...');
        aguardarProcessamento(estado);

        estado.etapa = 'transcrevendo';
        salvarEstado(estado);

        const transcricao = gerarTranscricao(estado);
        finalizarProcessamento(estado, transcricao);
        break;

      case 'transcrevendo':
        Logger.log('🔄 Retentando transcrição...');
        const transcricaoRetry = gerarTranscricao(estado);
        finalizarProcessamento(estado, transcricaoRetry);
        break;

      default:
        Logger.log(`⚠️ Estado desconhecido: ${estado.etapa}. Reiniciando.`);
        limparEstado();
    }
  } catch (err) {
    Logger.log(`❌ Erro ao continuar: ${err.message}`);
    estado.tentativas = (estado.tentativas || 0) + 1;

    if (estado.tentativas >= 3) {
      Logger.log('❌ Máximo de tentativas. Abandonando arquivo.');
      limparEstado();
    } else {
      salvarEstado(estado);
    }
  }
}

function finalizarProcessamento(estado, transcricao) {
  const CFG = getCfg();

  if (transcricao && transcricao.length > 10) {
    const file = DriveApp.getFileById(estado.fileId);
    const tema = extrairTema(transcricao);
    const docUrl = criarDocumentoTranscricao(estado.fileName, tema, transcricao);

    file.setDescription((file.getDescription() || '') + ' | processado');

    const folder = DriveApp.getFolderById(CFG.FOLDER_ID);
    const subpastaProcessados = obterOuCriarSubpasta(folder, 'processados');
    moverParaSubpasta(file, folder, subpastaProcessados);

    Logger.log(`🎉 SUCESSO! Documento: ${docUrl}`);
  }

  limparArquivoGemini(estado.fileServerName);
  limparEstado();
}

// ============ FUNÇÕES DE UPLOAD ============

function iniciarUpload(audioInfo) {
  const CFG = getCfg();

  const initRes = UrlFetchApp.fetch(
    `https://generativelanguage.googleapis.com/upload/v1beta/files?key=${CFG.GEMINI_KEY}`,
    {
      method: 'post',
      headers: {
        'X-Goog-Upload-Protocol': 'resumable',
        'X-Goog-Upload-Command': 'start',
        'X-Goog-Upload-Header-Content-Length': audioInfo.fileSize.toString(),
        'X-Goog-Upload-Header-Content-Type': audioInfo.mimeType,
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify({ file: { displayName: audioInfo.fileName } })
    }
  );

  const uploadUrl = initRes.getHeaders()['X-Goog-Upload-URL'] || initRes.getHeaders()['x-goog-upload-url'];

  return { uploadUrl };
}

function enviarChunks(estado) {
  const CFG = getCfg();
  const authToken = ScriptApp.getOAuthToken();
  const chunkSize = 8 * 1024 * 1024;

  let start = estado.uploadOffset || 0;
  let fileInfo = null;

  while (start < estado.fileSize) {
    let end = Math.min(start + chunkSize, estado.fileSize);

    const chunkData = UrlFetchApp.fetch(
      `https://www.googleapis.com/drive/v3/files/${estado.fileId}?alt=media`,
      {
        method: 'get',
        headers: {
          'Authorization': 'Bearer ' + authToken,
          'Range': `bytes=${start}-${end - 1}`
        }
      }
    ).getContent();

    const res = UrlFetchApp.fetch(estado.uploadUrl, {
      method: 'post',
      headers: {
        'X-Goog-Upload-Command': (end === estado.fileSize) ? 'upload, finalize' : 'upload',
        'X-Goog-Upload-Offset': start.toString()
      },
      payload: chunkData,
      muteHttpExceptions: true
    });

    if (end === estado.fileSize) {
      fileInfo = JSON.parse(res.getContentText());
    }

    start = end;
    estado.uploadOffset = start;
    salvarEstado(estado);

    const progresso = ((start / estado.fileSize) * 100).toFixed(0);
    Logger.log(`   Upload: ${progresso}%`);
  }

  return fileInfo;
}

function aguardarProcessamento(estado) {
  const CFG = getCfg();

  let status = "PROCESSING";
  let tentativas = 0;

  while (status === "PROCESSING" && tentativas < CFG.MAX_POLLING_TENTATIVAS) {
    Utilities.sleep(CFG.POLLING_INTERVALO_MS);

    const check = JSON.parse(
      UrlFetchApp.fetch(
        `https://generativelanguage.googleapis.com/v1beta/${estado.fileServerName}?key=${CFG.GEMINI_KEY}`
      ).getContentText()
    );

    status = check.state;
    tentativas++;

    const tempoDecorrido = tentativas * (CFG.POLLING_INTERVALO_MS / 1000);
    Logger.log(`   Status: ${status} (${tempoDecorrido}s)`);

    if (tentativas % 6 === 0) {
      estado.pollingTentativas = tentativas;
      salvarEstado(estado);
    }
  }

  if (status !== "ACTIVE") {
    throw new Error(`Arquivo não ficou pronto. Status final: ${status}`);
  }
}

function gerarTranscricao(estado) {
  const CFG = getCfg();

  const response = UrlFetchApp.fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${CFG.GEMINI_MODEL}:generateContent?key=${CFG.GEMINI_KEY}`,
    {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({
        contents: [{
          role: 'user',
          parts: [
            {
              text: 'Transcreva este áudio integralmente em português do Brasil. Identifique os diferentes oradores (ex: Orador 1, Orador 2) sempre que a voz mudar. Formate como: "Orador X: [fala]". Retorne APENAS a transcrição, sem comentários ou análises.'
            },
            {
              fileData: {
                mimeType: estado.mimeType,
                fileUri: estado.fileUri
              }
            }
          ]
        }]
      })
    }
  );

  const result = JSON.parse(response.getContentText());
  return result.candidates[0].content.parts[0].text;
}

function limparArquivoGemini(fileServerName) {
  const CFG = getCfg();

  try {
    UrlFetchApp.fetch(
      `https://generativelanguage.googleapis.com/v1beta/${fileServerName}?key=${CFG.GEMINI_KEY}`,
      { method: 'delete' }
    );
  } catch (e) {
    // Ignora erros de limpeza
  }
}

// ============ FUNÇÕES AUXILIARES ============

function obterOuCriarSubpasta(pastaRaiz, nomeSub) {
  const subpastas = pastaRaiz.getFoldersByName(nomeSub);
  if (subpastas.hasNext()) {
    return subpastas.next();
  }
  return pastaRaiz.createFolder(nomeSub);
}

function moverParaSubpasta(file, pastaOrigem, pastaDestino) {
  try {
    pastaDestino.addFile(file);
    pastaOrigem.removeFile(file);
    Logger.log(`📦 Arquivo movido para "${pastaDestino.getName()}/"`);
  } catch (e) {
    Logger.log(`⚠️ Erro ao mover arquivo: ${e.message}`);
  }
}

function extrairTema(transcricao) {
  const CFG = getCfg();

  const prompt = `Analise esta transcrição e retorne APENAS um título curto (máximo 40 caracteres) que descreva o tema principal da conversa. Sem aspas, sem explicações, apenas o título.

TRANSCRIÇÃO (primeiros 2000 chars):
${transcricao.substring(0, 2000)}`;

  try {
    const res = UrlFetchApp.fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${CFG.GEMINI_MODEL}:generateContent?key=${CFG.GEMINI_KEY}`,
      {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify({
          contents: [{ role: 'user', parts: [{ text: prompt }] }]
        })
      }
    );

    let tema = JSON.parse(res.getContentText()).candidates[0].content.parts[0].text.trim();
    tema = tema.replace(/["\n\r]/g, '').substring(0, 40);
    return tema;
  } catch (e) {
    Logger.log(`⚠️ Erro ao extrair tema: ${e.message}`);
    return 'Reunião';
  }
}

function criarDocumentoTranscricao(originalName, tema, transcricao) {
  const CFG = getCfg();
  const dateStr = Utilities.formatDate(new Date(), CFG.TIMEZONE, 'yyyy-MM-dd');
  const titulo = `${dateStr} — ${tema}`.substring(0, 100);

  const doc = DocumentApp.create(titulo);
  const body = doc.getBody();

  body.appendParagraph(`Transcrição: ${originalName}`).setHeading(DocumentApp.ParagraphHeading.HEADING2);
  body.appendParagraph(`Data: ${dateStr}`);
  body.appendParagraph(`Tema: ${tema}`);
  body.appendHorizontalRule();

  body.appendParagraph("TRANSCRIÇÃO").setHeading(DocumentApp.ParagraphHeading.HEADING1);
  body.appendParagraph(transcricao);

  doc.saveAndClose();

  if (CFG.OUTPUT_FOLDER_ID) {
    try {
      const file = DriveApp.getFileById(doc.getId());
      DriveApp.getFolderById(CFG.OUTPUT_FOLDER_ID).addFile(file);
      DriveApp.getRootFolder().removeFile(file);
    } catch (e) {
      Logger.log("⚠️ Documento criado, mas erro ao mover para pasta de saída.");
    }
  }

  return doc.getUrl();
}

// ============ FUNÇÕES DE DIAGNÓSTICO ============

function verStatusFila() {
  const fila = obterFila();
  const estado = obterEstado();

  Logger.log('═══════════════════════════════════════');
  Logger.log('📊 STATUS DO SISTEMA DE TRANSCRIÇÃO');
  Logger.log('═══════════════════════════════════════');
  Logger.log(`📋 Arquivos na fila: ${fila.length}`);

  if (fila.length > 0) {
    Logger.log('\nPróximos na fila:');
    fila.slice(0, 5).forEach((item, i) => {
      Logger.log(`   ${i + 1}. ${item.fileName}`);
    });
    if (fila.length > 5) {
      Logger.log(`   ... e mais ${fila.length - 5} arquivos`);
    }
  }

  Logger.log('\n🔄 Estado atual:');
  if (estado) {
    Logger.log(`   Arquivo: ${estado.fileName}`);
    Logger.log(`   Etapa: ${estado.etapa}`);
    Logger.log(`   Iniciado em: ${estado.iniciadoEm}`);
    if (estado.erro) {
      Logger.log(`   ⚠️ Erro: ${estado.erro}`);
      Logger.log(`   Tentativas: ${estado.tentativas || 0}/3`);
    }
  } else {
    Logger.log('   Nenhum processamento em andamento');
  }

  Logger.log('═══════════════════════════════════════');
}

function limparFilaCompleta() {
  salvarFila([]);
  limparEstado();
  Logger.log('🗑️ Fila e estado limpos completamente.');
}

function forcarReprocessamento(fileId) {
  limparEstado();

  const file = DriveApp.getFileById(fileId);
  const desc = file.getDescription() || '';
  file.setDescription(desc.replace(/\s*\|\s*processado/gi, ''));

  Logger.log(`🔄 Arquivo ${file.getName()} marcado para reprocessamento.`);
  Logger.log('Execute enfileirarAudios() para adicioná-lo à fila.');
}
