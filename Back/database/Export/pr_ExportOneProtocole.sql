
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'pr_ExportOneProtocole')
	DROP PROCEDURE pr_ExportOneProtocole
GO



CREATE PROCEDURE [dbo].[pr_ExportOneProtocole] 
	(
	@ProtocoleType INT
	)
AS
BEGIN
	IF object_id('TmpObsExport') IS NOT NULL
			DROP TABLE TmpObsExport


	DECLARE @ProtocoleName VARCHAR(255)


	SELECT @ProtocoleName = Name from [EcoReleve_ECWP].dbo.ProtocoleType where id=@ProtocoleType
	print 'Export ' + @ProtocoleName

	---------------------- CREATION DE LA TABLE CIBLE

	-- Ges Static Prop
	select O.* into TmpObsExport 
	from [EcoReleve_ECWP].dbo.Observation O
	where O.FK_ProtocoleType = @ProtocoleType
	
	exec pr_ExportObservationDynPropValueNow
	
	
	DECLARE @Req NVARCHAR(MAX)
	DECLARE @ReqFrom NVARCHAR(MAX)
	DECLARE @ReqSet NVARCHAR(MAX)
	SET @Req = ' CREATE UNIQUE CLUSTERED INDEX PK_TProtocol'  +  replace(@ProtocoleName,' ','_') + ' ON TmpObsExport (ID)' 
	exec ( @req)
	IF EXISTS (select * from [EcoReleve_ECWP].dbo.ObservationDynProp D JOIN [EcoReleve_ECWP].dbo.ProtocoleType_ObservationDynProp C ON C.FK_ProtocoleType = @ProtocoleType and c.FK_ObservationDynProp =D.ID )
	BEGIN
		-- ALTER WITH DYN PROPS
		SET @Req = ' ALTER TABLE TmpObsExport ADD@'

		select @Req = @Req + ',    ' +  replace(D.Name,' ','_') + ' ' + replace(replace(d.typeProp,'Integer','INT'),'string','varchar(255)')  
		from [EcoReleve_ECWP].dbo.ObservationDynProp D JOIN [EcoReleve_ECWP].dbo.ProtocoleType_ObservationDynProp C ON C.FK_ProtocoleType = @ProtocoleType and c.FK_ObservationDynProp =D.ID

		SET @Req = replace(@Req,'ADD@,','ADD ')
		--print @Req
		exec ( @req)
	

		IF EXISTS(SELECT * from TmpObsExport)
		BEGIN
			-- UPDATE DATA FROM DYN PROP

			SET @ReqSet = 'SET@'
			SET @ReqFrom =''


			SELECT @ReqSet = @ReqSet + ',' + replace(P.Name,' ','_') + '=(select Value' +  replace(P.TypeProp,'Integer','Int') + ' FROM   TObservationDynPropValueNow  where fk_observationdynprop=' + convert(varchar(10),P.ID) + ' and fk_observation = EI.ID)'
			--SELECT @ReqSet = @ReqSet + ',' + replace(P.Name,' ','_') + '=V.' + replace(P.Name,' ','_'), @ReqFrom = @ReqFrom + ',MAX(CASE WHEN Name=''' +  replace(P.Name,' ','_') + ''' THEN Value' + replace(P.TypeProp,'Integer','Int') + ' ELSE NULL END) ' + replace(P.Name,' ','_')
			from [EcoReleve_ECWP].dbo.ObservationDynProp P JOIN [EcoReleve_ECWP].dbo.ProtocoleType_ObservationDynProp C ON C.FK_ProtocoleType = @ProtocoleType and c.FK_ObservationDynProp =P.ID 


			SET @ReqSet = replace(@ReqSet,'SET@,','SET ')
			SET @Req = 'UPDATE EI ' + @ReqSet +  ' FROM TmpObsExport EI '



			--SELECT @ReqSet = @ReqSet + ',' + replace(P.Name,' ','_') + '=V.' + replace(P.Name,' ','_'), @ReqFrom = @ReqFrom + ',MAX(CASE WHEN Name=''' +  replace(P.Name,' ','_') + ''' THEN Value' + replace(P.TypeProp,'Integer','Int') + ' ELSE NULL END) ' + replace(P.Name,' ','_')																						
			--from [EcoReleve_ECWP].dbo.ObservationDynProp P JOIN [EcoReleve_ECWP].dbo.ProtocoleType_ObservationDynProp C ON C.FK_ProtocoleType = @ProtocoleType and c.FK_ObservationDynProp =P.ID 


			--SET @ReqSet = replace(@ReqSet,'SET@,','SET ')
			--print @ReqFrom

			--SET @Req = 'UPDATE EI ' + @ReqSet +  ' FROM TmpObsExport EI JOIN (SELECT VN.FK_Observation ' + @ReqFrom + ' FROM   [EcoReleve_ECWP].dbo.ObservationDynPropValuesNow VN GROUP BY VN.FK_Observation) V ON EI.ID = V.FK_Observation '

			--SET @Req = 'SELECT * FROM TmpIndivExport EI JOIN (SELECT VN.FK_Individual ' + @ReqFrom + ' FROM   [EcoReleve_ECWP].dbo.IndividualDynPropValuesNow VN GROUP BY VN.FK_Individual) V ON EI.ID = V.FK_Individual '

			print @req

			exec ( @req)
		END	
	END
	SET @Req = ' IF object_id(''TProtocol_'  +  replace(@ProtocoleName,' ','_') + ''') IS NOT NULL DROP TABLE  TProtocol_'  +  replace(@ProtocoleName,' ','_')
	exec ( @req)
	SET @Req = ' sp_rename ''TmpObsExport'' ,TProtocol_'  +  replace(@ProtocoleName,' ','_')

	exec ( @req)

END







