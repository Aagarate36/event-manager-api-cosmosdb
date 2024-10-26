from fastapi import FastAPI, HTTPException, Query, Path
from typing import List, Optional
from database import container
from models import Evento, Participante
from azure.cosmos import exceptions
from datetime import datetime

app = FastAPI(title='API de Gestion de Eventos y Participantes')

###Endpoint de Eventos

@app.get("/")
def home():
	return "Hola Mundo"

	
###Crear evento
@app.post("/events/",response_model=Evento,status_code=201)
def create_event(event: Evento):
	try:
		container.create_item(body=event.dict())
		return event
	except exceptions.CosmosResourceExistError:
		raise HTTPException(status_code=400, detail="El evento con este ID ya existe.")
	except exceptions.CosmosHttpResponseError as e:
		raise HTTPException(status_code=400, detail=str(e))


		#Obtener evento por id
@app.get("/events/{event_id}", response_model=Evento)
def get_event(event_id: str= Path(...,description="ID del evento a recuperar")):
	try:
		evento=container.read_item(item=event_id,partition_key=event_id)
		return event
	except exceptions.CosmosResourceNotFoundError:
		raise HTTPException(status_code=404, detail="El evento no encontrado.")
	except exceptions.CosmosHttpResponseError as e:
		raise HTTPException(status_code=400, detail=str(e))


##Listar eventos

@app.get("/events/", response_model=List[Evento])
def list_envent():
	query="SELECT * FROM c WHERE 1=1"
	items=list(container.query_items(query=query,enable_cross_partition_query=True))
	return items

	# Actualizar evento
@app.put("/events/{event_id}", response_model=Evento)
def update_event(event_id: str, updated_event: Evento):
	existing_event = container.read_item(item=event_id, partition_key= event_id)
	existing_event.update(updated_event.dict(exclude_unset=True))
	
	if existing_event['capacity'] < len(existing_event['participants']):
		print("La capacidad no puede ser menor que el numero de participantes actuales")
		return
	try:
		container.replace_item(item = event_id, body = existing_event)
		return existing_event
	except exceptions.CosmosResourceNotFoundError:
		raise HTTPException(status_code=404, detail="Producto no encontrado")
	except exceptions.CosmosHttpResponseError as e:
		raise HTTPException(status_code=400, detail= str(e))