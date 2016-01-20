from ..Models import Base,DBSession
from sqlalchemy import (Column
    , DateTime
    , Float
    , ForeignKey
    , Index
    , Integer
    , Numeric
    , String
    , Text
    , Unicode
    , text
    ,Sequence
    ,select
    , and_
    , or_
    ,distinct
    ,asc)
from sqlalchemy.dialects.mssql.base import BIT
from sqlalchemy.orm import relationship
from collections import OrderedDict
from datetime import datetime
from .FrontModules import FrontModules,ModuleForms, ModuleGrids
import transaction
from operator import itemgetter
from collections import OrderedDict
from traceback import print_exc
from pyramid import threadlocal
from ..utils.datetime import parse
from ..utils.parseValue import parseValue,find,isEqual


Cle = {'String':'ValueString','Float':'ValueFloat','Date':'ValueDate','Integer':'ValueInt','float':'ValueFloat'}

class ObjectWithDynProp:
    ''' Class to extend for mapped object with dynamic properties '''
    PropDynValuesOfNow = {}
    allProp = None

    def __init__(self,ObjContext=None):
        self.ObjContext = threadlocal.get_current_request().dbsession
        self.PropDynValuesOfNow = {}
        self.GetAllProp()

    def GetAllProp (self) :
        ''' Get all object properties (dynamic and static) '''
        if self.allProp is None:
            try :
                #### IF typeObj is setted retrieve only dynamic props of this type ####
                type_ = self.GetType()
            except :
                #### ELSE retrieve all dyn props ####
                type_ = None
            dynPropTable = Base.metadata.tables[self.GetDynPropTable()]
            if type_ :
                result = type_.GetDynProps()
            else :
                result = self.ObjContext.execute(select([dynPropTable])).fetchall()
            statProps = [{'name': statProp.key, 'type': statProp.type} for statProp in self.__table__.columns ]
            dynProps = [{'name':dynProp.Name,'type':dynProp.TypeProp}for dynProp in result]
            statProps.extend(dynProps)
            self.allProp = statProps
        return self.allProp

    def GetPropWithName(self,nameProp):
        if self.allProp is None:
            self.GetAllProp()
        return find(lambda x: x['name'].lower() == nameProp.lower(),self.allProp)

    def GetFrontModulesID (self,ModuleType) :
        if not hasattr(self,'FrontModules') :
            self.FrontModules = self.ObjContext.query(FrontModules).filter(FrontModules.Name==ModuleType).one()
        return self.FrontModules.ID

    def GetGridFields (self,ModuleType):
        ''' Function to call : return Name and Type of Grid fields to display in front end 
        according to configuration in table ModuleGrids'''
        try:
            typeID = self.GetType().ID
            gridFields = self.ObjContext.query(ModuleGrids
            ).filter(and_(ModuleGrids.Module_ID == self.GetFrontModulesID(ModuleType),
                or_(ModuleGrids.TypeObj == typeID ,ModuleGrids.TypeObj ==None ))
            ).order_by(asc(ModuleGrids.GridOrder)).all()
        except:
            gridFields = self.ObjContext.query(ModuleGrids).filter(
                ModuleGrids.Module_ID == self.GetFrontModulesID(ModuleType)
                ).order_by(asc(ModuleGrids.GridOrder)).all()

        gridFields.sort(key=lambda x: str(x.GridOrder))
        cols = []
        #### return only fileds existing in conf ####
        for curConf in gridFields:
            curConfName = curConf.Name
            gridField = list(filter(lambda x : x['name'] == curConfName,self.GetAllProp()))
            if len(gridField)>0 :
                cols.append(curConf.GenerateColumn())
            elif curConf.QueryName is not None:
                cols.append(curConf.GenerateColumn())
            elif curConf.Name == 'StartDate':
                cols.append(curConf.GenerateColumn())

        # for curProp in self.GetAllProp():
        #     curPropName = curProp['name']
        #     gridField = list(filter(lambda x : x.Name == curPropName,gridFields))
        #     if len(gridField)>0 :
        #         cols.append(gridField[0].GenerateColumn())
        return cols

    def GetFilters (self,ModuleType) :
        ''' Function to call : return Name and Type of Filters to display in front end 
        according to configuration in table ModuleGrids'''
        filters = []
        defaultFilters = []
        try:
            typeID = self.GetType().ID
            filterFields = self.ObjContext.query(ModuleGrids).filter(
                and_(
                    ModuleGrids.Module_ID == self.GetFrontModulesID(ModuleType)
                    , or_( ModuleGrids.TypeObj == typeID,ModuleGrids.TypeObj == None)
                    )).order_by(asc(ModuleGrids.FilterOrder)).all()
        except :
            filterFields = self.ObjContext.query(ModuleGrids
                ).filter(ModuleGrids.Module_ID == self.GetFrontModulesID(ModuleType)).order_by(asc(ModuleGrids.FilterOrder)).all()  #.order_by(asc(ModuleGrids.FilterOrder)).all()


        # filterFields.sort(key=lambda x: str(x.FilterOrder))
        for curConf in filterFields:
            curConfName = curConf.Name
            filterField = list(filter(lambda x : x['name'] == curConfName
                and curConf.IsSearchable == 1 ,self.GetAllProp()))

            if len(filterField)>0 :
                filters.append(curConf.GenerateFilter())
            elif curConf.QueryName is not None:
                filters.append(curConf.GenerateFilter())
        #### OLD VERSION ####
        # for curProp in self.allProp:
        #     curPropName = curProp['name']
        #     filterField = list(filter(lambda x : x.Name == curPropName
        #         and x.IsSearchable == 1 ,filterFields))

        #     if len(filterField)>0 :
        #         filters.append(filterField[0].GenerateFilter())

            # elif len(list(filter(lambda x : x.Name == curPropName, filterFields))) == 0:
            #     filter_ = {
            #     'name' : curPropName,
            #     'label' : curPropName,
            #     'type' : 'Text'
            #     }
        return filters

    def GetType(self):
        raise Exception("GetType not implemented in children")

    def GetDynPropValuesTable(self):
        return self.__tablename__ + 'DynPropValue'

    def GetDynPropValuesTableID(self):
        return 'ID'

    def GetMyIDName(self):
        return 'ID'

    def GetDynPropTable(self):
        return self.__tablename__ + 'DynProp'

    def GetDynPropFKName(self):
        return 'FK_' + self.__tablename__ + 'DynProp'

    # def GetSelfFKName(self):
    #     return 'FK_' + self.__tablename__ + 'DynProp'  ###### ====> Not used , the same thing as GetDynPropFKName Why ??

    def GetSelfFKNameInValueTable(self):
        return 'FK_' + self.__tablename__

    def GetpkValue(self) :
        return self.ID

    def GetProperty(self,nameProp) :
        try :
            return getattr(self,nameProp)
        except :
            return self.PropDynValuesOfNow[nameProp]

    def SetProperty(self,nameProp,valeur) :
        ''' Set object properties (static and dynamic) '''
        if hasattr(self,nameProp):
            try :
                if nameProp in self.__table__.c:
                    curTypeAttr = str(self.__table__.c[nameProp].type).split('(')[0]
                    if 'date' in curTypeAttr.lower() :
                        try:
                            valeur = parse(valeur.replace(' ',''))
                        except:
                            pass
                setattr(self,nameProp,valeur)
            except :
                pass
        else:
            if (nameProp.lower() in self.GetType().DynPropNames):
                if (nameProp not in self.PropDynValuesOfNow #and parseValue(valeur)!= None
                    ) or (isEqual(self.PropDynValuesOfNow[nameProp],valeur) is False):
                    #### IF no value or different existing value, new value is affected ####
                    if 'date' in self.GetPropWithName(nameProp)['type'].lower():
                        try:
                            valeur = parse(valeur.replace(' ',''))
                        except:
                            pass
                    NouvelleValeur = self.GetNewValue(nameProp)
                    NouvelleValeur.StartDate = datetime.today()
                    setattr(NouvelleValeur,Cle[self.GetPropWithName(nameProp)['type']],valeur)
                    self.PropDynValuesOfNow[nameProp] = valeur
                    self.GetDynPropValues().append(NouvelleValeur)
                else:
                    # print('valeur non modifiée pour ' + nameProp)
                    return

            else :
                print('propriété inconnue ' + nameProp)
                return
                # si la propriété dynamique existe déjà et que la valeur à affectée est identique à la valeur existente
                # => alors on insére pas d'historique car pas de chanegement

    def GetNewValue(self):
        raise Exception("GetNewValue not implemented in children")

    def LoadNowValues(self):
        curQuery = 'select V.*, P.Name,P.TypeProp from ' + self.GetDynPropValuesTable() + ' V JOIN ' + self.GetDynPropTable() + ' P ON P.' + self.GetDynPropValuesTableID() + '= V.' + self.GetDynPropFKName() + ' where '
        curQuery += 'not exists (select * from ' + self.GetDynPropValuesTable() + ' V2 '
        curQuery += 'where V2.' + self.GetDynPropFKName() + ' = V.' + self.GetDynPropFKName() + ' and V2.' + self.GetSelfFKNameInValueTable() + ' = V.' + self.GetSelfFKNameInValueTable() + ' '
        curQuery += 'AND V2.startdate > V.startdate)'
        curQuery +=  'and v.' + self.GetSelfFKNameInValueTable() + ' =  ' + str(self.GetpkValue() )

        Values = self.ObjContext.execute(curQuery).fetchall()
        for curValue in Values :
            row = OrderedDict(curValue)
            self.PropDynValuesOfNow[row['Name']] = self.GetRealValue(row)

    def GetRealValue(self,row):
        return row[Cle[row['TypeProp']]]

    def UpdateFromJson(self,DTOObject):
        ''' Function to call : update properties of new or existing object with JSON/dict of value'''
        for curProp in DTOObject:
            #print('Affectation propriété ' + curProp)
            if (curProp.lower() != 'id' and DTOObject[curProp] != '-1' ):
                if isinstance(DTOObject[curProp],str) and len(DTOObject[curProp].split())==0:
                    DTOObject[curProp] = None
                self.SetProperty(curProp,DTOObject[curProp])

    def GetFlatObject(self,schema=None):
        ''' return flat object with static properties and last existing value of dyn props '''
        resultat = {}
        if self.ID is not None : 
            max_iter = max(len( self.__table__.columns),len(self.PropDynValuesOfNow))
            for i in range(max_iter) :
                #### Get static Properties ####
                try :
                    curStatProp = list(self.__table__.columns)[i]
                    resultat[curStatProp.key] = self.GetProperty(curStatProp.key)
                except :
                    pass
                #### Get dynamic Properties ####
                try :
                    curDynPropName = list(self.PropDynValuesOfNow)[i]
                    resultat[curDynPropName] = self.GetProperty(curDynPropName)
                except Exception as e :
                    pass
        else : 
            max_iter = len( self.__table__.columns)
            for i in range(max_iter) :
                #### Get static Properties ####
                try :
                    curStatProp = list(self.__table__.columns)[i]
                    curVal = self.GetProperty(curStatProp.key)
                    if curVal is not None :
                        resultat[curStatProp.key] = self.GetProperty(curStatProp.key)
                except :
                    pass
        # Add TypeName in JSON
        # resultat['TypeName'] = self.GetType().Name
        return resultat

    def GetSchemaFromStaticProps(self,FrontModules,DisplayMode):
        ''' return schema of static props to feed front end form '''
        Editable = (DisplayMode.lower()  == 'edit')
        resultat = {}
        type_ = self.GetType().ID
        Fields = self.ObjContext.query(ModuleForms
            ).filter(and_(ModuleForms.Module_ID == FrontModules.ID),ModuleForms.FormRender>0).order_by(ModuleForms.FormOrder).all()

        for curStatProp in self.__table__.columns:
            CurModuleForms = list(filter(lambda x : x.Name == curStatProp.key and x.FormRender>0 and (x.TypeObj== str(type_) or x.TypeObj == None) , Fields))
            if (len(CurModuleForms)> 0 ):
                # Conf définie dans FrontModules
                CurModuleForms = CurModuleForms[0]
                resultat[CurModuleForms.Name] = CurModuleForms.GetDTOFromConf(Editable)
        return resultat

    def GetDTOWithSchema(self,FrontModules,DisplayMode):
        ''' Function to call: return full schema according to configuration (table :ModuleForms) '''
        schema = self.GetSchemaFromStaticProps(FrontModules,DisplayMode)
        ObjType = self.GetType()
        ObjType.AddDynamicPropInSchemaDTO(schema,FrontModules,DisplayMode)

        resultat = {
            'schema':schema,
            'fieldsets' : ObjType.GetFieldSets(FrontModules,schema)
            }

        #### IF ID is send from front --> get data of this object in order to display value into form which will be sent ####
        data = self.GetFlatObject(schema)
        resultat['data'] = data
        if self.ID :
            resultat['data']['id'] = self.ID
            for key, value in schema.items():
                if (DisplayMode.lower() != 'edit' and schema[key]['fullPath'] is True):
                    try : 
                        resultat['data'][key] = self.splitFullPath(resultat['data'][key])
                    except : pass
        else :
            resultat['data']['id'] = 0
            # add default values for each field in data if exists
            #for attr in schema:
            for key, value in schema.items():
                if value['defaultValue'] is not None:
                    resultat['data'][key] = value['defaultValue']

        return resultat

    def splitFullPath(self,value):
        splitValue = value.split('>')[-1]
        return splitValue

